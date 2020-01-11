import tensorflow as tf
from tensorflow_probability import distributions as tfd
import sonnet as snt
import glob
import numpy as np
from datapipes.audiorecord_in import *
import math


def load_data(x):
    key, intervals, data_len = deserialize_example(x.numpy())
    sparse_indexes, sparse_weights = parse_sparse(intervals)
    sparse_ids = [x[1] for x in sparse_indexes]

    # can't return a SparseTensor from here...
    # we'll do the conversion to SparseTensor later
    return data_len, sparse_indexes, sparse_ids, sparse_weights


py_load_data = lambda x: tf.py_function(
    load_data, [x], [tf.int64, tf.int64, tf.int64, tf.float32])


def generate_dataset(data_len, sparse_indexes, sparse_ids, sparse_weights):
    shape = (data_len, index_end - index_start)
    ids = tf.sparse.SparseTensor(sparse_indexes, sparse_ids, shape)
    weights = tf.sparse.SparseTensor(sparse_indexes, sparse_weights, shape)

    return tf.data.Dataset.zip((
        tf.data.Dataset.from_tensor_slices(ids),
        tf.data.Dataset.from_tensor_slices(weights),
    ))


def input_db(archive_fn, batch_size):
    filenames = glob.glob(archive_fn)

    return (tf.data.TFRecordDataset(filenames).map(
        py_load_data, num_parallel_calls=tf.data.experimental.AUTOTUNE).cache(
        )  # must be done before repeat
            .repeat(None)  # must be done before shuffling
            .shuffle(batch_size * 2)  # must be done before flattenning
            .flat_map(generate_dataset)  # must be done before batching
            .batch(batch_size).prefetch(tf.data.experimental.AUTOTUNE))


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

        self.prior = tfd.MultivariateNormalDiag(loc=tf.zeros([latent_size]),
                                                scale_identity_multiplier=1.0)

        # self._lookup = LookupModule(500)
        self._encoder = snt.Linear(output_size=1500)
        self._latent_net = MultivarNormalDistModule(latent_size)

        self._decoder = snt.Linear(output_size=1500)
        self._sparse_net = NormalDistModule(index_end - index_start)

    # def lookup(self, ids, weights):
    # 	return self._lookup(ids, weights)

    def encode(self, features):
        hidden = self._encoder(features)
        return self._latent_net(hidden)

    def decode(self, latent_sample):
        hidden = self._decoder(latent_sample)
        return self._sparse_net(hidden)

    def loss(self, prior, latent_dist, target):
        latent_sample = latent_dist.sample()
        reconstruction = self.decode(latent_sample)

        recon_loss = -tf.concat([
            reconstruction.log_prob(target),
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

    def __call__(self, features):
        latent_dist = self.vae.encode(features)
        return latent_dist

    def gradients(self, features):
        with tf.GradientTape() as tape:
            latent_dist = self.vae.encode(features)
            loss = self.vae.loss(self.vae.prior, latent_dist, features)
            loss = tf.reduce_mean(loss)

        params = self.vae.trainable_variables
        grads = tape.gradient(loss, params)

        return loss, grads, params
