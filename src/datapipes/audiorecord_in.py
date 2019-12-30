import tensorflow as tf
import numpy as np
from datapipes.audiorecord_out import KNOWN_PHONEMES

KNOWN_TAGS = KNOWN_PHONEMES
NUM_TAGS = len(KNOWN_TAGS)
NUM_FLOATS = 10


def deserialize_example(raw_record):
	example = tf.train.Example()
	example.ParseFromString(raw_record)

	key = example.features.feature['key'].bytes_list.value[0]

	result = []
	for interval in example.features.feature['intervals'].bytes_list.value:
		interval_data = tf.train.Example()
		interval_data.ParseFromString(interval)
		result.append(interval_data)

	return key, result, len(result)

def parse_floats(intervals, data_len):
	float_features = np.zeros(shape=(data_len, NUM_FLOATS), dtype=np.float)
	float_mask = np.zeros(shape=(data_len, NUM_FLOATS), dtype=np.float)

	for i, intvl in enumerate(intervals):
		float_features[i,0] = intvl.features.feature['pitch'].float_list.value[1]
		float_features[i,1] = intvl.features.feature['pitch'].float_list.value[2]
		float_features[i,2] = intvl.features.feature['intensity'].float_list.value[1]
		float_features[i,3] = intvl.features.feature['gci'].float_list.value[0]
		float_features[i,4] = intvl.features.feature['f1'].float_list.value[1]
		float_features[i,5] = intvl.features.feature['f1'].float_list.value[2]
		float_features[i,6] = intvl.features.feature['f2'].float_list.value[1]
		float_features[i,7] = intvl.features.feature['f2'].float_list.value[2]
		float_features[i,8] = intvl.features.feature['f3'].float_list.value[1]
		float_features[i,9] = intvl.features.feature['f3'].float_list.value[2]

		float_mask[i,0] = intvl.features.feature['pitch'].float_list.value[0]
		float_mask[i,1] = intvl.features.feature['pitch'].float_list.value[0]
		float_mask[i,2] = intvl.features.feature['intensity'].float_list.value[0]
		float_mask[i,3] = 1.0 # gci count, always present
		float_mask[i,4] = intvl.features.feature['f1'].float_list.value[0]
		float_mask[i,5] = intvl.features.feature['f1'].float_list.value[0]
		float_mask[i,6] = intvl.features.feature['f2'].float_list.value[0]
		float_mask[i,7] = intvl.features.feature['f2'].float_list.value[0]
		float_mask[i,8] = intvl.features.feature['f3'].float_list.value[0]
		float_mask[i,9] = intvl.features.feature['f3'].float_list.value[0]
		
	return float_features, float_mask

def _to_strings(bytes_list):
	return [x.decode('utf-8') for x in bytes_list]


def parse_tags(intervals):
	phoneme_idx_start = 0

	tag_values = []
	tag_mask = []

	for i, intvl in enumerate(intervals):
		phonemes = _to_strings(intvl.features.feature['phonemes'].bytes_list.value[:])
		for j, phoneme in enumerate(phonemes):
			tag_values.append(phoneme)
			tag_mask.append((i, phoneme_idx_start + j))

	return tag_values, tag_mask


