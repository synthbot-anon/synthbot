import tensorflow as tf
import numpy as np
from datapipes.audiorecord_out import (ALL_INDEXES, POSITION_IDX, PHONEME_IDX,
                                       PITCH_IDX, INTENSITY_IDX, GCI_IDX,
                                       FORMANT_IDX, CHARACTER_IDX, TAG_IDX,
                                       NOISE_IDX)


def _get_bounds(idx):
    values = idx.values()
    return min(values), max(values) + 1


index_start, index_end = 0, len(ALL_INDEXES)
position_start, position_end = _get_bounds(POSITION_IDX)
phoneme_start, phoneme_end = _get_bounds(PHONEME_IDX)
pitch_start, pitch_end = _get_bounds(PITCH_IDX)
intensity_start, intensity_end = _get_bounds(INTENSITY_IDX)
gci_start, gci_end = _get_bounds(GCI_IDX)
formant_start, formant_end = _get_bounds(FORMANT_IDX)
character_start, character_end = _get_bounds(CHARACTER_IDX)
tag_start, tag_end = _get_bounds(TAG_IDX)
noise_start, noise_end = _get_bounds(NOISE_IDX)


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


def parse_sparse(intervals):
    indexes = []
    weights = []

    for i, intvl in enumerate(intervals):
        indexes.extend([
            (i, x)
            for x in intvl.features.feature['sparse_indexes'].int64_list.value
        ])
        weights.extend([
            x
            for x in intvl.features.feature['sparse_weights'].float_list.value
        ])

    return indexes, weights
