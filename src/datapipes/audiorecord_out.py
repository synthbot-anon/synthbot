import itertools
import tensorflow as tf
import numpy as np
import math


KNOWN_PHONEMES = set(['AA', 'AE', 'AH', 'AO', 'AW', 'AY', 
	'B', 'CH',  'D', 'DH', 'EH', 'ER', 'EY', 'F', 'G',
	'HH', 'IH', 'IY', 'JH', 'K', 'L', 'M', 'N', 'NG',
	'OW', 'OY', 'P', 'R', 'S', 'SH', 'T', 'TH', 'UH',
	'UW', 'V', 'W', 'Y', 'Z', 'ZH', 'sil', 'sp'])

ARTICULATION_PLACES = {
}

ARTICULATION_MANNERS = {
}

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

	return result
		
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


def get_tags(label):
	for tag in label['tags']:
		yield tag


def _median_feature(data, default):
	data = np.array(list(data), dtype=float)
	result = np.median(data, axis=0)
	
	if result.shape == ():
		if math.isnan(result):
			return _float_feature(default)
		return _float_feature([1, result])
	else:
		return _float_feature([1, *result])
			

def _phone_feature(phonemes):
	result = []
	for phm in phonemes:
		assert phm in KNOWN_PHONEMES
		result.append(phm.encode('utf-8'))
	
	result = _bytes_feature(result)
	return result


def _interval_string(label, info, start, end):
	f1, f2, f3 = get_formants(info, start, end)

	feature = {
		'phonemes': _phone_feature(get_phones(label, start, end)),
		# tags
		'pitch': _median_feature(get_pitch(info, start, end), [0, 0, 0]),
		'intensity': _median_feature(get_intensity(info, start, end), [0, 0]),
		'gci': _float_feature([get_gcis(info, start, end)]),
		'f1': _median_feature(f1, [0, 0, 0]),
		'f2': _median_feature(f2, [0, 0, 0]),
		'f3': _median_feature(f3, [0, 0, 0]),
	}
	
	example_proto = tf.train.Example(features=tf.train.Features(feature=feature))
	return example_proto.SerializeToString()


def _clip_length(label):
	start, end = label['utterance']['episode_interval']
	return end - start

def _serialize_example(key, label, info):
	intervals = []
	end = _clip_length(label)
	for i, start in enumerate(np.arange(0, end, 0.05)):
		intervals.append(_interval_string(label, info, start, start + 0.05))

	feature = {
		'key': _bytes_feature([key.encode('utf-8')]),
		'intervals': _bytes_feature(intervals)
	}

	example_proto = tf.train.Example(features=tf.train.Features(feature=feature))
	return example_proto.SerializeToString()

serialize_example = _serialize_example

class LabelRecordGenerator:
	def __init__(self, output_file, clips_per_shard=24000):
		self.path = output_file.path
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


