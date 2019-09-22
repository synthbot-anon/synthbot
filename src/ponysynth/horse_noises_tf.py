import tensorflow as tf
import sonnet as snt

from ponysynth.horse_noises import _generate_examples
import tarfile
import os
import json

tf.enable_v2_behavior()
tf.enable_eager_execution()

def _generate_examples(tgz_path):
	archive = tarfile.open(tgz_path, mode='r:gz')
	retrieved_examples = {}

	for item in archive:
		filename = item.name
		key = os.path.dirname(filename)
		filename = os.path.basename(filename)

		if key not in retrieved_examples:
			retrieved_examples[key] = {}
		example = retrieved_examples[key]

		name, ext = os.path.splitext(filename)
		example[name] = item

	for key, value in retrieved_examples.items():
		audio = archive.extractfile(value['audio'])
		label = archive.extractfile(value['label'])

		result = json.loads(label.read().decode('utf-8'))
		result['utterance']['episode_interval'] = [float(x) for x in result['utterance']['episode_interval']]
		result['audio'] = audio.read()
		result['clip_id'] = key

		yield result

def _tf_clip_generator(tgz_path):
	for example in _generate_examples(tgz_path):
		yield {
			'clip_id': example['clip_id'],
			'wav': example['audio'],
			'character': example['character'],
			'episode': example['episode'],
			'tags': example['tags'],
			'noise': example['noise'],
			'utterance': tuple(example['utterance'].values()),
			'words.content': [x['content'] for x in example['words']],
			'words.loc':
				[[x[0], x[1]] for x in 
					[y['interval'] for y in example['words']]],
			'phones.content': [x['content'] for x in example['phones']],
			'phones.loc': 
				[[x[0], x[1]] for x in 
					[y['interval'] for y in example['words']]],
		}

def _tfds_clips(tgz_path):
	generator = lambda: _tf_clip_generator(tgz_path)
	return tf.data.Dataset.from_generator(generator,
		output_types={
			'clip_id': tf.string,
			'wav': tf.string,
			'character': tf.string,
			'episode': tf.string,
			'tags': tf.string,
			'noise': tf.string,
			'utterance': (tf.string, tf.float32),
			'words.content': tf.string,
			'words.loc': tf.float32,
			'phones.content': tf.string,
			'phones.loc': tf.float32
		})

def _decode_wav(clip):
	samples, rate = tf.audio.decode_wav(clip['wav'])
	rate = tf.cast(rate, tf.float32)
	
	del clip['wav']
	clip['samples'] = samples
	clip['rate'] = rate

	for key in clip:
		if key.endswith('.loc'):
			clip[key] = tf.cast(rate * clip[key], tf.int32)
	
	return clip

def _get_phones(clip):
	return 

def _get_diphones(clip):
	pass


def _generate_phone_refs(tfds):
	tf.map_fn(_get_phones)

# interchangeability based on high level, minimal assumptions, api
# "this is an rnn, conforms to some api, just drop it in and it works"
# composability
# decouple module definition from module training
# hackability
# optimize for research

# training setup: "how do you set up the data, launch experiments, monitor them"
# "what configurability is there for the researchers"
# the model implementation should be orthogonal to all of this