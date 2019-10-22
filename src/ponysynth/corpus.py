import itertools
import os
import re
from typing import *
import tarfile
import json
import random
import io

import librosa # type: ignore
import soundfile
import numpy

from ponysynth.indexes import SubstringIndex


class ClipperArchive:
	def __init__(self, archive_path):
		self._archive = tarfile.open(archive_path, mode='r')
		self._tarobjects = _load_tar_objects(self._archive)

	def read_label(self, key):
		file = self._archive.extractfile(self._tarobjects[key]['label'])
		data = json.loads(file.read().decode('utf-8'))
		data['key'] = key
		return data

	def read_audio(self, key):
		file = self._archive.extractfile(self._tarobjects[key]['audio'])
		return file

	def labels(self):
		for key in self._tarobjects.keys():
			yield self.read_label(key)

	def audio(self):
		for key in self._tarobjects.keys():
			yield self.read_audio(key)


class SpeechCorpus:
	def __init__(self, archive_path):
		self.archive = ClipperArchive(archive_path)
		self._phone_idx = None

	def build_phone_index(self, substrIdx=SubstringIndex):
		self._phone_idx = substrIdx()

		for label in self.archive.labels():
			phones = [x['content'] for x in label['phones']]
			self._phone_idx.index(phones, label)

	def nphones(self, n):
		assert self._phone_idx != None

		def _gen():
			for utterance, offset in self._phone_idx.read_layer(height=n):
				yield (utterance, offset, 3)

		return PhoneSeqs(self, _gen())

	def phones(self):
		return self.nphones(1)

	def diphones(self):
		return self.nphones(2)

	def triphones(self):
		return self.nphones(3)

	def phoneseqs(self, phonemes):
		def _gen():
			length = len(phonemes)
			for utterance, offset in self._phone_idx.find(phonemes):
				yield (utterance, offset, length)

		return PhoneSeqs(self, _gen())


def _iter_sample_fast(iterable, samplesize):
	"""
	From DzinX on https://stackoverflow.com/questions/12581437
	Take random samples from a generator.
	"""
	results = []
	iterator = iter(iterable)
	# Fill in the first samplesize elements:
	try:
		for _ in range(samplesize):
			results.append(next(iterator))
	except StopIteration:
		raise ValueError("Sample larger than population.")
	random.shuffle(results)  # Randomize their positions
	for i, v in enumerate(iterator, samplesize):
		r = random.randint(0, i)
		if r < samplesize:
			results[r] = v  # at a decreasing rate, replace random items
	return (x for x in results)


class PhoneSeqs:
	def __init__(self, corpus, generator):
		self.corpus = corpus
		self.generator = generator

	def sample(self, k=1):
		return PhoneSeqs(self.corpus, _iter_sample_fast(self.generator, k))

	def __iter__(self):
		return (PhoneSeq(self.corpus, *x) for x in self.generator)

	def cache(self):
		return PhoneSeqsCache(self.corpus, list(self.generator))

class PhoneSeqsCache:
	def __init__(self, corpus, cache):
		self.corpus = corpus
		self.cache = cache

	def sample(self, k=1):
		return [PhoneSeq(self.corpus, *x) for x in random.sample(self.cache, k=k)]

	def __iter__(self):
		return (PhoneSeq(self.corpus, *x) for x in self.cache)

	def __next__(self):
		return PhoneSeq(self.corpus, *self.cache[0])

	def __getitem__(self, index):
		return PhoneSeq(self.corpus, *self.cache[index])

	def __len__(self):
		return len(self.cache)


class PhoneSeq:
	def __init__(self, corpus, clip, offset, length):
		self.corpus = corpus
		self.clip = clip
		self.offset = offset
		self.length = length

	def _phones(self):
		start = self.offset
		end = self.offset + self.length
		return self.clip['phones'][start:end]

	def intervals(self):
		start = self.offset
		end = self.offset + self.length

		clip_intervals = [x['interval'] for x in self._phones()]
		seq_start = clip_intervals[0][0]
		return numpy.array(clip_intervals) - seq_start

	def phonemes(self):
		return tuple((x['content'] for x in self._phones()))

	def diphonemes(self):
		phonemes = self.phonemes()
		diphonemes = zip(phonemes[:-1], phonemes[1:])
		
		return tuple(diphonemes)

	def audio(self):
		utterance = self.corpus.archive.read_audio(self.clip['key'])
		samples, rate = librosa.core.load(utterance, sr=None)

		intervals = [x['interval'] for x in self._phones()]
		start, _ = intervals[0]
		_, end = intervals[-1]

		start_idx = int(start * rate)
		end_idx = int(end * rate)
		return samples[start_idx:end_idx], rate

	def utterance(self):
		return PhoneSeq(self.corpus, self.clip, 0, len(self.clip['phones']))

def _load_tar_objects(archive):
	result = {}

	for item in archive:
		filename = item.name
		key = os.path.dirname(filename)
		filename = os.path.basename(filename)

		if key not in result:
			result[key] = {}
		example = result[key]

		name, ext = os.path.splitext(filename)
		example[name] = item

	return result
