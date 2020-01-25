import librosa
import numpy
import scipy
import matplotlib.pyplot as plt
from IPython import display as ipd

class ClipBot:
	def __init__(self, samples, rate):
		self.base_samples = samples
		self.rate = rate

		self.start_time = 0.0
		self.start_idx = 0
		self.end_time = len(samples) / float(rate)
		self.end_idx = len(samples)


		self.draw = ClipDrawBot(self)
		self.mod = ClipModBot(self)

	def sub(self, start_time, end_time):
		result = ClipBot(self.base_samples, self.rate)

		result.start_time = start_time
		result.start_idx = int(start_time * self.rate)
		result.end_time = end_time
		result.end_idx = int(end_time * self.rate)

		return result

	def subidx(self, start_idx, end_idx):
		result = ClipBot(self.base_samples, self.rate)

		result.start_time = float(start_idx) / self.rate
		result.start_idx = start_idx
		result.end_time = float(end_idx) / self.rate
		result.end_idx = end_idx

		return result

	def split(self, *times):
		indexes = [int(x * self.rate) for x in times]
		starts = [self.start_idx] + indexes
		ends = indexes + [self.end_idx]
		bounds = zip(starts, ends)

		return [self.subidx(x,y) for x,y in bounds]

	def words(self, label):
		result = []
		for candidate in label['words']:
			if (candidate['interval'][0] >= self.start_time
				or candidate['interval'][1] <= self.end_time):
				result.append(candidate['content'])

		return ' '.join(result)

	def first_word(self, label):
		end_time = label['words'][0]['interval'][-1]
		return self.sub(0, end_time)

	def last_word(self, label):
		start_time = label['words'][-1]['interval'][0]
		end_time = label['phones'][-1]['interval'][-1]
		return self.sub(start_time, end_time)

	def get_samples(self):
		return self.base_samples[self.start_idx:self.end_idx]

	def get_times(self):
		size = len(self.get_samples())
		return numpy.arange(size, dtype='float') / self.rate


def crossfade(pre_samples, post_samples, t):
	pre_signal = scipy.signal.hilbert(pre_samples)
	post_signal = scipy.signal.hilbert(post_samples)

	return numpy.sqrt(pre_signal**2 * (1-t) + post_signal**2 * t)

class ClipModBot:
	def __init__(self, clipbot):
		self.clip = clipbot

	def crossfade(self, pre=None, post=None):
		samples = self.clip.get_samples()
		print(self.clip.end_idx)
		print(self.clip.start_idx)
		t = numpy.arange(len(samples)) / len(samples)

		if pre == None:
			pre_samples = samples
		else:
			pre_samples = pre(t)

		if post == None:
			post_samples = samples
		else:
			post_samples = post(t)

		composed = crossfade(pre_samples, post_samples, t)

		bounds = numpy.arange(self.clip.start_idx, self.clip.end_idx)

		print('bounds:', bounds)
		print('samples:', samples.shape)
		print('composed:', composed.shape)
		self.clip.base_samples[bounds] = numpy.real(composed)

		return composed

class ClipDrawBot:
	def __init__(self, clipbot):
		self.clip = clipbot

	def envelope(self):
		samples = self.clip.get_samples()
		analytical_signal = scipy.signal.hilbert(samples)
		envelope = numpy.abs(analytical_signal)

		plt.plot(envelope)

	def figure(self, figsize=(15,3)):
		plt.figure(figsize=figsize)

	def samples(self):
		plt.plot(self.clip.get_times(), self.clip.get_samples())
		plt.xlabel('time')
		plt.ylabel('pcm')

	def audio(self):
		samples = self.clip.get_samples()
		ipd.display(ipd.Audio(samples, rate=self.clip.rate))

	def show(self):
		plt.show()

	# def mark(self, *times, desc=[]):
	# 	if desc != []:
	# 		assert len(times) == len(desc)

	# 	previous_delta = 0
	# 	for i, t in enumerate(times):
	# 		delta = t - self.clip.start_time
	# 		middle = (delta + previous_delta) / 2.0
	# 		plt.axvline(x=delta)
	# 		plt.text((middle


