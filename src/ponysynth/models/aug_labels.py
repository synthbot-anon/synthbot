import tensorflow as tf
from tensorflow_probability import distributions as tfd
import sonnet as snt
import glob
import numpy as np
from datapipes.audiorecord_in import *

# start and stop tokens
KNOWN_MARKERS = ('start', 'stop')
NUM_MARKERS = len(KNOWN_MARKERS)
NUM_TAGS = len(KNOWN_TAGS)


def generate_markers(data_len):
	marker_values = KNOWN_MARKERS
	marker_mask = [
		(0, 0),
		(data_len-1, 1)
	]
	return marker_values, marker_mask

def load_data(x):
	key, intervals, data_len = deserialize_example(x.numpy())

	float_features, float_mask = parse_floats(intervals, data_len)
	tag_values, tag_mask = parse_tags(intervals)
	marker_values, marker_mask = generate_markers(data_len)

	# can't return a SparseTensor from here...
	# we'll do the conversion to SparseTensor later

	return data_len, float_features, float_mask, tag_values, tag_mask, marker_values, marker_mask


_py_load_data = lambda x: tf.py_function(load_data, [x],
	[tf.int64, tf.float32, tf.float32, tf.string, tf.int64, tf.string, tf.int64])


def generate_dataset(data_len, float_features, float_mask, tag_values, tag_mask, marker_values, marker_mask):
	tag_shape = (data_len, NUM_TAGS)
	tag_features = tf.sparse.SparseTensor(tag_mask, tag_values, tag_shape)
	marker_shape = (data_len, NUM_MARKERS)
	marker_features = tf.sparse.SparseTensor(marker_mask, marker_values, marker_shape)
	
	return tf.data.Dataset.zip((
		tf.data.Dataset.from_tensor_slices(float_features),
		tf.data.Dataset.from_tensor_slices(float_mask),
		tf.data.Dataset.from_tensor_slices(tag_features),
		tf.data.Dataset.from_tensor_slices(marker_features)
	))

def feature_columns():
	# create columns to represent input types
	floats_category = tf.feature_column.numeric_column(
		'floats', shape=(NUM_FLOATS,))
	float_mask_category = tf.feature_column.numeric_column(
		'float_mask', shape=(NUM_FLOATS,))
	tags_category = tf.feature_column.categorical_column_with_vocabulary_list(
		'tags', tuple(KNOWN_TAGS))
	markers_category = tf.feature_column.categorical_column_with_vocabulary_list(
		'markers', KNOWN_MARKERS)

	# feature columns for the embedding vector
	embedding_features = []
	embedding_features.append(floats_category)
	embedding_features.append(float_mask_category)
	embedding_features.append(tf.feature_column.indicator_column(tags_category))
	embedding_features.append(tf.feature_column.indicator_column(markers_category))

	return embedding_features


def _to_model_input_fn(batch_size):
	def _gen(float_features, float_mask, tag_features, marker_features):
		float_features.set_shape((batch_size, NUM_FLOATS))
		float_mask.set_shape((batch_size, NUM_FLOATS))

		features = {
			'floats': float_features,
			'float_mask': float_mask,
			'tags': tag_features,
			'markers': marker_features
		}
		return features

	return _gen

def input_db(archive_fn, batch_size):
	filenames = glob.glob(archive_fn)
	
	return (tf.data.TFRecordDataset(filenames)
		.map(_py_load_data, num_parallel_calls=16)
		.cache() # must be done before repeat
		.repeat(None)
		.shuffle(batch_size*2) # must be done after repeat
		.flat_map(generate_dataset) # must be done after shuffling
		.batch(batch_size)
		.map(_to_model_input_fn(batch_size)) # the result uses a lot of memory
		.prefetch(tf.data.experimental.AUTOTUNE))


class MultivarNormalDistModule(snt.Module):
	def __init__(self, output_size, name=None):
		super(MultivarNormalDistModule, self).__init__(name=name)
		self._means_net = snt.Linear(output_size)
		self._stdevs_net = snt.Linear(output_size)

	def __call__(self, features):
		means = self._means_net(features)
		stdevs = tf.math.abs(self._stdevs_net(features))
		return tfd.MultivariateNormalDiag(loc=means, scale_diag=stdevs)

class NormalDistModule(snt.Module):
	def __init__(self, output_size, name=None):
		super(NormalDistModule, self).__init__(name=name)
		self._means_net = snt.Linear(output_size)
		self._stdevs_net = snt.Linear(output_size)

	def __call__(self, features):
		means = self._means_net(features)
		stdevs = tf.math.abs(self._stdevs_net(features))
		return tfd.Normal(loc=means, scale=stdevs)

class BernoulliDistModule(snt.Module):
	def __init__(self, output_size, name=None):
		super(BernoulliDistModule, self).__init__(name=name)
		self._logits_net = snt.Linear(output_size)

	def __call__(self, features):
		logits = self._logits_net(features)
		return tfd.Bernoulli(logits=logits)


class SimpleVAE(snt.Module):
	def __init__(self, latent_size, name=None):
		super(SimpleVAE, self).__init__(name=name)
		
		self.prior = tfd.MultivariateNormalDiag(
			loc=tf.zeros([latent_size]),
			scale_identity_multiplier=1.0)

		self._encoder = snt.Linear(output_size=500)
		self._latent_net = MultivarNormalDistModule(latent_size)

		self._decoder = snt.Linear(output_size=500)
		self._floats_net = NormalDistModule(NUM_FLOATS)
		self._tags_net = BernoulliDistModule(NUM_TAGS)
		self._markers_net = BernoulliDistModule(NUM_MARKERS)

	def encode(self, features):
		hidden = self._encoder(features)
		return self._latent_net(hidden)

	def decode(self, latent_sample):
		hidden = self._decoder(latent_sample)
		return {
			'floats': self._floats_net(hidden),
			'tags': self._tags_net(hidden),
			'markers': self._markers_net(hidden)
		}

	def split_features(self, features):
		floats_start = 0
		floats_end = floats_start + NUM_FLOATS
		float_mask_start = floats_end
		float_mask_end = float_mask_start + NUM_FLOATS
		tags_start = float_mask_end
		tags_end = tags_start + NUM_TAGS
		markers_start = tags_end
		markers_end = markers_start + NUM_MARKERS

		return {
			'floats': features[:,floats_start:floats_end],
			'float_mask': features[:,float_mask_start:float_mask_end],
			'tags': features[:,tags_start:tags_end],
			'markers': features[:,markers_start:markers_end]
		}

	def loss(self, prior, latent_dist, features):
		latent_sample = latent_dist.sample()
		reconstruction = self.decode(latent_sample)
		target = self.split_features(features)

		recon_loss = -tf.concat([
			reconstruction['floats'].log_prob(target['floats']),
			reconstruction['tags'].log_prob(target['tags']),
			reconstruction['markers'].log_prob(target['markers']),
		], axis=1)

		recon_loss = tf.clip_by_value(recon_loss, -1e5, 1e5)
		recon_loss = tf.reduce_sum(recon_loss)
		
		latent_loss = tfd.kl_divergence(latent_dist, self.prior)
		latent_loss = tf.clip_by_value(latent_loss, -1e5, 1e5)

		return latent_loss + recon_loss


class VAEModel(tf.keras.Model):
	def __init__(self, vae):
		super(VAEModel, self).__init__()
		self.vae = vae

	def __call__(self, inputs):
		latent_dist = self.vae.encode(inputs)
		return latent_dist

	def gradients(self, batch):
		with tf.GradientTape() as tape:
			latent_dist = self.vae.encode(batch)
			loss = self.vae.loss(self.vae.prior, latent_dist, batch)
			loss = tf.reduce_mean(loss)

		params = self.vae.trainable_variables
		grads = tape.gradient(loss, params)

		return loss, zip(grads, params)