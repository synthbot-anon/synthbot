import itertools
from functools import reduce
from math import ceil
from typing import *

import numpy # type: ignore
from pandas import Interval # type: ignore

def interval(start, end):
	# TODO: define a custom interval class that enforces these restrictions
	assert end >= start
	return Interval(float(start), float(end), closed='both')

_empty_interval = interval(0, 0)
_empty_array = numpy.array([], dtype=numpy.float32)

class SoundSheaf:
	# A soundsheaf is a differentiable function from time to frames (time -> frames)
	def __init__(self, frames: numpy.ndarray = _empty_array, interval: Interval = _empty_interval):
		if len(frames) == 0:
			assert interval == _empty_interval

		self._frames = frames
		self.interval = interval
		self._baselength = interval.length

	def subsheaf(self, subinterval):
		result = SoundSheaf(self._frames, subinterval)
		result._baselength = self._baselength
		return result

	def get_image(self):
		size = len(self._frames)
		start = int(self.interval.left / self._baselength * size)
		end = ceil(self.interval.right / self._baselength * size)
		return self._frames[start:end]

def __is_overlapping(pre: SoundSheaf, post: SoundSheaf):
	if numpy.any(pre._frames != post._frames):
		return False
	if not pre.interval.overlaps(post.interval):
		return False
	return True

def merge_sheaves(pre: SoundSheaf, post: SoundSheaf):
	if pre.interval == _empty_interval:
		return post
	if post.interval == _empty_interval:
		return pre

	if __is_overlapping(pre, post):
		merged_interval = interval(pre.interval.left, post.interval.right)

		result = SoundSheaf(pre._frames, merged_interval)
		result._baselength = pre._baselength
		return result
	else:
		frames = numpy.concatenate([pre.get_image(), post.get_image()])
		merged_interval = interval(0, pre.interval.length + post.interval.length)
		result = SoundSheaf(frames, merged_interval)
		return result

# TODO: Flesh this out
Content = str

class Utterance:
	# A monoid of phones composed through diphones

	def __init__(self, phones: Sequence['Phone'] = [], diphones: Sequence['Diphone'] = []):
		assert phones != None
		assert diphones != None

		if len(phones) == 0:
			assert len(diphones) == 0
			self.phones = [] # type: List[Phone]
			self.diphones = [] # type: List[Diphone]
			return

		assert len(phones) == len(diphones) + 1
		# make sure overlapping sounds agree on the intended overlap in content
		for connector, pre, post in zip(diphones, phones[:-1], phones[1:]):
			assert connector.pre.content == pre.content, \
				"Expected '{}' but found '{}'".format(connector.pre.content, pre.content)
			assert connector.post.content == post.content, \
				"Expected '{}' but found '{}'".format(connector.post.content, post.content)

		self.phones = list(phones)
		self.diphones = list(diphones)

	def get_start_time(self):
		return self.phones[0].sheaf.interval.left

	def get_end_time(self):
		return self.phones[-1].sheaf.interval.right

	def get_sheaf(self):
		sheaves = [[x.pre.sheaf, x.sheaf] for x in self.diphones]
		sheaves.append([self.phones[-1].sheaf])
		sheaves = itertools.chain(*sheaves)

		return reduce(merge_sheaves, sheaves, SoundSheaf())

	def get_content(self):
		return [x.content for x in self.phones]


	def subutterance(self, start: int, end: int):
		if start == end:
			return Utterance(phones=[], diphones=[])

		assert start >= 0 and start < end
		assert end > start and end <= len(self.phones)

		subphones = self.phones[start:end]
		subdiphones = self.diphones[start:end-1]
		return Utterance(phones=subphones, diphones=subdiphones)

class Phone(Utterance):
	# A phone is a soundsheaf indexed by phone content. Phone content determines 
	# whether two sounds are intended to be equivalent.

	def __init__(self, content: Content, sheaf: SoundSheaf):
		assert content != None and sheaf != None
		self.content = content
		self.sheaf = sheaf
		Utterance.__init__(self, [self], [])

class DiphoneSequence:
	# A monoid of diphones.

	def __init__(self, diphones: Sequence['Diphone'] = []):
		if diphones == []:
			self.diphones = [] # type: List[Diphone]
			self.phones = [] # type: List[Phone]
			return

		# make sure adjacent diphones agree on the intended overlap between contents
		for pre, post in zip(diphones[:-1], diphones[1:]):
			assert pre.post.content == post.pre.content
		
		self.diphones = list(diphones)
		self.phones = [x.pre for x in diphones]
		self.phones.extend([diphones[-1].post])


class Diphone(DiphoneSequence):
	# A diphone is the soundsheaf representation of an transition between two phones
	def __init__(self, pre: Phone, post: Phone, sheaf: SoundSheaf):
		assert pre != None and post != None and sheaf != None
		self.pre = pre
		self.post = post
		self.sheaf = sheaf
		DiphoneSequence.__init__(self, [self])

def merge_diphseq(pre: DiphoneSequence, post: DiphoneSequence) -> DiphoneSequence:
	combined_diphones = pre.diphones + post.diphones
	return DiphoneSequence(combined_diphones)

def merge_utterances(
		pre: Utterance, transition: DiphoneSequence, post: Utterance) -> Utterance:
	if len(transition.diphones) == 0:
		assert pre == post
		return pre

	assert transition.diphones[0].pre.content == pre.phones[-1].content
	assert transition.diphones[-1].post.content == post.phones[0].content

	combined_phones = pre.phones + transition.phones[1:-1] + post.phones
	combined_diphones = pre.diphones + transition.diphones + post.diphones

	return Utterance(combined_phones, combined_diphones)
