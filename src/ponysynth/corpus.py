import itertools
import os
import re
from typing import *
import tarfile
import json
import random
import io

import librosa # type: ignore

from ponysynth.indexes import SubstringIndex
from ponysynth.sound_sheaf import *


class ClipperArchive:
	def __init__(self, archive_path):
		self._archive = tarfile.open(archive_path, mode='r:gz')
		self._tarobjects = _load_tar_objects(self._archive)

	def read_label(self, key):
		file = self._archive.extractfile(self._tarobjects[key]['label'])
		data = json.loads(file.read().decode('utf-8'))
		data['key'] = key
		return data

	def read_audio(self, key):
		file = self._archive.extractfile(self._tarobjects[key]['audio'])
		data = file.read()
		return data

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

	def diphones(self):
		assert self._phone_idx != None

		def _gen():
			for utterance, offset in self._phone_idx.read_layer(height=2):
				yield (utterance, offset, 2)

		return PhoneSeqs(self, _gen())

	def triphones(self):
		assert self._phone_idx != None

		def _gen():
			for utterance, offset in self._phone_idx.read_layer(height=3):
				yield (utterance, offset, 3)

		return PhoneSeqs(self, _gen())

	def phoneseqs(self, phonemes):
		def _gen():
			length = len(phonemes)
			for utterance, offset in self._phone_idx.find(phonemes):
				yield (utterance, offset, length)

		return PhoneSeqs(self, _gen())


# From DzinX on https://stackoverflow.com/questions/12581437
def _iter_sample_fast(iterable, samplesize):
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
		return self

	def __next__(self):
		return PhoneSeq(self.corpus, *next(self.generator))

	
class PhoneSeq:
	def __init__(self, corpus, clip, offset, length):
		self.corpus = corpus
		self.clip = clip
		self.offset = offset
		self.length = length

	def phones(self):
		start = self.offset
		end = self.offset + self.length

		return self.clip['phones'][start:end]
	
	def phonemes(self):
		return (x['content'] for x in self.phones())

	def diphonemes(self):
		phonemes = [x['content'] for x in self.phones()]
		diphonemes = zip(phonemes[:-1], phonemes[1:])
		
		return diphonemes

	def audio(self):
		utterance = self.corpus.archive.read_audio(self.clip['key'])
		samples, rate = librosa.core.load(io.BytesIO(utterance), sr=None)

		phones = self.phones()
		start, _ = phones[0]['interval']
		_, end = phones[-1]['interval']

		print(self.clip['key'])
		print(phones)

		start_idx = int(start * rate)
		end_idx = int(end * rate)
		return samples[start_idx:end_idx], rate

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
