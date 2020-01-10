import itertools
import tensorflow as tf
import numpy as np
import math

from datapipes.clipper_in import CHARACTERS, TAGS, NOISE


TOTAL_IDX = 0
ALL_INDEXES = []


def _index_tags(category, tags):
	global TOTAL_IDX

	tags = sorted(tags)

	result = dict(dict(zip(tags, range(
		TOTAL_IDX, TOTAL_IDX + len(tags)))))
	TOTAL_IDX += len(tags)
	ALL_INDEXES.extend([f'{category}:{x}' for x in tags])

	return result


KNOWN_POSITIONS = set(['start', 'stop'])
POSITION_IDX = _index_tags('position', KNOWN_POSITIONS)
KNOWN_PHONEMES = set(['AA', 'AE', 'AH', 'AO', 'AW', 'AY', 
	'B', 'CH',  'D', 'DH', 'EH', 'ER', 'EY', 'F', 'G',
	'HH', 'IH', 'IY', 'JH', 'K', 'L', 'M', 'N', 'NG',
	'OW', 'OY', 'P', 'R', 'S', 'SH', 'T', 'TH', 'UH',
	'UW', 'V', 'W', 'Y', 'Z', 'ZH', 'sil', 'sp'])
PHONEME_IDX = _index_tags('phoneme', KNOWN_PHONEMES)
PITCH_IDX = _index_tags('pitch', ['freq.hz', 'strength.corr'])
INTENSITY_IDX = _index_tags('intensity', ['volume.db'])
GCI_IDX = _index_tags('voicing', ['gci.count'])
FORMANT_IDX = _index_tags('formant', [
	'f1:centre.hz', 'f1:bandwidth.hz',
	'f2:centre.hz', 'f2:bandwidth.hz',
	'f3:centre.hz', 'f3:bandwidth.hz'])
CHARACTER_IDX = _index_tags('character', 
	[x.replace(' ', '-') for x in CHARACTERS.values()])
TAG_IDX = _index_tags('tag', TAGS)
NOISE_IDX = _index_tags('noise', NOISE.values())


def _bytes_feature(value):
	"""Returns a bytes_list from a string / byte."""
	return tf.train.Feature(bytes_list=tf.train.BytesList(value=value))


def _float_feature(value):
	"""Returns a float_list from a float / double."""
	return tf.train.Feature(float_list=tf.train.FloatList(value=value))


def _int64_feature(value):
	"""Returns an int64_list from a bool / enum / int / uint."""
	return tf.train.Feature(int64_list=tf.train.Int64List(value=value))


def get_phones(label, start, end):
	result = set()

	for phone in label['phones']:
		phone_start = float(phone['interval'][0])
		phone_end = float(phone['interval'][1])
		
		if phone_start <= end and phone_end >= start:
			content = phone['content']
			if content[-1] in ('0', '1', '2'):
				content = content[:-1]
			result.add(content)
		# convert to place of articulation
		# convert to manner of articulation

	# these need to be sorted to be used as sparse matrix indices
	return sorted(result)


def get_pitch(info, start, end):
	for pitch in info['pitch']:
		pitch_time = float(pitch['time.sec'])
		if pitch_time >= start and pitch_time < end:
			yield pitch['pitch.hz'], pitch['strength.corr']


def get_intensity(info, start, end):	  
	for intensity in info['intensity']:
		intensity_time = float(intensity['time.sec'])
		if intensity_time >= start and intensity_time < end:
			yield intensity['volume.db']


def get_gcis(info, start, end):
	result = 0
	
	for gci in info['gci.sec']:
		gci_time = float(gci)
		if gci_time >= start and gci_time < end:
			result += 1
	
	return result


def get_formants(info, start, end):
	f1 = []
	f2 = []
	f3 = []
	
	for formants in info['formants']:
		formant_time = float(formants['time.sec'])
		if formant_time >= start and formant_time < end:
			if 'F1' in formants:
				f1.append((formants['F1']['centre.hz'], formants['F1']['bandwidth.hz']))
			if 'F2' in formants:
				f2.append((formants['F2']['centre.hz'], formants['F2']['bandwidth.hz']))
			if 'F3' in formants:
				f3.append((formants['F3']['centre.hz'], formants['F3']['bandwidth.hz']))
	
	return f1, f2, f3


def _median(data):
	data = np.array(list(data), dtype=float)
	if len(data) == 0:
		return []

	return np.median(data, axis=0)
			

def _interval_string(label, info, start, end):
	# the feature order needs to match the order of indices

	sparse_indexes = []
	sparse_weights = []
	dense_weights = []

	# position
	if start == 0:
		sparse_indexes.append(POSITION_IDX['start'])
		sparse_weights.append(1)

	clip_end = label['utterance']['episode_interval']
	duration = clip_end[1] - clip_end[0]
	if end >= duration:
		sparse_indexes.append(POSITION_IDX['stop'])
		sparse_weights.append(1)

	# phonemes
	phonemes = get_phones(label, start, end)
	sparse_indexes.extend([PHONEME_IDX[x] for x in phonemes])
	sparse_weights.extend([1 for x in phonemes])

	# pitch
	pitch = _median(get_pitch(info, start, end))
	if len(pitch) > 0:
		sparse_indexes.append(PITCH_IDX['freq.hz'])
		sparse_weights.append(pitch[0])
		sparse_indexes.append(PITCH_IDX['strength.corr'])
		sparse_weights.append(pitch[1])

	# intensity
	intensity = _median(get_intensity(info, start, end))
	if intensity:
		sparse_indexes.append(INTENSITY_IDX['volume.db'])
		sparse_weights.append(intensity)

	# closure instances
	gci = get_gcis(info, start, end)
	if gci:
		sparse_indexes.append(GCI_IDX['gci.count'])
		sparse_weights.append(gci)

	# formants
	formants = get_formants(info, start, end)
	def _add_formant(n, formant):
		sparse_indexes.append(FORMANT_IDX[f'f{n}:bandwidth.hz'])
		sparse_weights.append(_median(formant)[1])
		sparse_indexes.append(FORMANT_IDX[f'f{n}:centre.hz'])
		sparse_weights.append(_median(formant)[0])
	
	for i, f in enumerate(formants, 1):
		if f:
			_add_formant(i, f)

	# character
	sparse_indexes.append(CHARACTER_IDX[label['character']])
	sparse_weights.append(1)

	# tags
	tags = sorted(label['tags'])
	sparse_indexes.extend([TAG_IDX[x] for x in tags])
	sparse_weights.extend([1 for x in tags])

	# noise
	if label['noise']:
		sparse_indexes.append(NOISE_IDX[label['noise']])
		sparse_weights.append(1)

	return sparse_indexes, sparse_weights


def _clip_length(label):
	start, end = label['utterance']['episode_interval']
	return end - start


def _serialize_example(key, label, info):
	index0 = []
	index1 = []
	weights = []

	end = _clip_length(label)
	for i, start in enumerate(np.arange(0, end, 0.05)):
		interval_indexes, interval_weights = _interval_string(label, info, start, start + 0.05)
		index0.extend([i for x in interval_indexes])
		index1.extend(interval_indexes)
		weights.extend(interval_weights)

	feature = {
		'key': _bytes_feature([key.encode('utf-8')]),
		'shape': _int64_feature([i+1, len(ALL_INDEXES)]),
		'index0': _int64_feature(index0),
		'index1': _int64_feature(index1),
		'weights': _float_feature(weights)
	}

	example_proto = tf.train.Example(features=tf.train.Features(feature=feature))
	return example_proto.SerializeToString()


class LabelRecordGenerator:
	def __init__(self, output_path, clips_per_shard=24000):
		self.path = output_path
		self.clips_per_shard = clips_per_shard

	def generate_result(self, audio_archive, info_archive):
		def load_by_key(clip_id):
			clip_id = clip_id.experimental_ref().deref().numpy().decode('utf-8')
			label = audio_archive.read_label(clip_id)
			info = info_archive.read_info(clip_id)
			return _serialize_example(clip_id, label, info)

		def tf_load_by_key(clip_id):
			[example,] = tf.py_function(load_by_key, [clip_id], [tf.string])
			return example

		def reduce_func(key, dataset):
			filename = tf.strings.join([self.path, tf.strings.as_string(key)])
			writer = tf.data.experimental.TFRecordWriter(filename)
			writer.write(dataset.map(lambda _, x: x))
			return tf.data.Dataset.from_tensors(filename)

		dataset = list(audio_archive.keys())
		n_shards = math.ceil(len(dataset) / self.clips_per_shard)
		dataset = tf.convert_to_tensor(dataset)
		dataset = tf.data.Dataset.from_tensor_slices(dataset)

		dataset = dataset.map(tf_load_by_key, 1)
		dataset = dataset.enumerate()
		dataset = dataset.apply(tf.data.experimental.group_by_window(
			lambda i, _: i % n_shards, reduce_func, tf.int64.max))

		for elem in dataset:
			pass
