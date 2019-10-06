import itertools

import librosa
import numpy
import tensorflow as tf

import ponysynth.pyglottal as pyglottal


def dataset(corpus, size=None):
	return {
		'generator': lambda: _dataset_gen(corpus, size),
		'output_types': {'sample': tf.float32, 'label': tf.int16}
	}

def _dataset_gen(corpus, size=None):
	real_triphones = corpus.triphones().cache()
	if size != None:
		real_triphones = real_triphones.sample(size)

	# goal: create fake triphones similar to the real ones
	# triphones -> diphones -> similar diphones -> similar triphone

	# first find out which diphonemes we're working with
	diphonemes = [x.diphonemes() for x in real_triphones]
	diphonemes = itertools.chain(*diphonemes)
	# get a list of usable diphones from the corpus
	diphones = dict([(x, corpus.phoneseqs(x).cache()) for x in diphonemes])

	# generate the fake triphones from the diphones we found
	# use the real triphones as a template
	for fake_triphone, rate, stitch_range in _fake_triphone_audio(real_triphones, diphones):
		# return the fake triphones as samples (class 1 ~ fake)
		yield {
			'sample.pcm': fake_triphone,
			'sample.rate': rate,
			'stitch.range': stitch_range
		}

def _fake_triphone_audio(template, diphones):
	# triphone -> diphonemes -> alternative diphones -> similar triphone
	# (H EH0 L) -> (H, EH0) (EH0 L) -> (H EH0)' (EH0 L)' -> (H EH0 L)'
	for tri in template:
		diphm1, diphm2 = tri.diphonemes()
		diph1 = diphones[diphm1].sample(1)[0]
		diph2 = diphones[diphm2].sample(1)[0]
		
		yield _merge_diphones_badly(diph1, diph2)

def _merge_diphones_badly(diph1, diph2):
	# we'll end up using half a phone at the end of the first diphone
	# and half a phone at the beginnign of the second diphone
	# ... make sure they're two halves of the same kind of whole
	assert diph1.phonemes()[-1] == diph2.phonemes()[0]

	# load audio samples for these diphones
	audio1, rate = diph1.audio()
	audio2, rate2 = diph2.audio()
	assert rate == rate2

	# find points to stitch these diphones together
	# this stiches them at the midpoints of the last / first phones
	# TODO: replace this heuristic with a neural network
	break1 = int(rate * diph1.intervals()[-1].mean())
	break2 = int(rate * diph2.intervals()[0].mean())

	# TODO: normalize the two clips for volume, pitch, pace, etc

	# stitch the diphones together
	part1 = audio1[:break1]
	part2 = audio2[break2:]
	sample_pcm = numpy.concatenate([part1, part2])

	# indexes (with border) where the audio is joined
	stitch_range = (len(part1)-1, len(part1))

	return sample_pcm, rate, stitch_range

def preprocess(generator, output_types):
	return {
		'generator': lambda: ({
			**preprocess_single(example['sample.pcm'], example['sample.rate']),
			'sample.pcm': example['sample.pcm'],
			'sample.rate': example['sample.rate'],
			'stitch.range': tf.constant(example['stitch.range'], dtype=tf.int16)
		} for example in generator()),
		'output_types': {
			'pitch.mean': tf.float32,
			'pitch.std': tf.float32,
			'pitch.rate': tf.int32,
			'pacing.wavelength': tf.float32,
			'volume.decibals': tf.float32,
			'volume.rate': tf.int32,
			'sample.pcm': tf.float32,
			'sample.rate': tf.int32,
			'stitch.range': tf.int32
		}
	}

def preprocess_single(pcm, sample_rate):
	return {
		**_pitch_information(pcm, sample_rate),
		**_pacing_information(pcm, sample_rate),
		**_volume_information(pcm, sample_rate)
	}

def _pitch_information(pcm, sample_rate):
	stfts = librosa.stft(pcm,
		win_length=960, hop_length=240, n_fft=960)
	pitches, magnitude = librosa.piptrack(S=stfts, sr=sample_rate)

	total_magnitude = numpy.maximum(magnitude.sum(axis=0), 1)
	
	weighted_pitches = pitches * magnitude
	mean_pitches = weighted_pitches.sum(axis=0) / total_magnitude
	
	centered_pitches = pitches - mean_pitches
	var_pitches = centered_pitches ** 2
	var_pitches = (var_pitches * magnitude).sum(axis=0) / total_magnitude
	std_pitches = numpy.sqrt(var_pitches)

	return {
		'pitch.mean': mean_pitches.astype(numpy.float32),
		'pitch.std': std_pitches.astype(numpy.float32),
		'pitch.rate': sample_rate / 240
	}

def _pacing_information(pcm, sample_rate):
	pitch_marks = numpy.array(pyglottal.quick_gci(pcm)).flatten()
	wavelengths = pitch_marks[1:] - pitch_marks[:-1]
	
	return {
		'pacing.wavelength': wavelengths.astype(numpy.float32)
	}

def _volume_information(pcm, sample_rate):
	# TODO: consider using https://github.com/keunwoochoi/perceptual_weighting
	cqts = librosa.cqt(pcm, sample_rate, hop_length=2**6,
		fmin=32.70, n_bins=84, bins_per_octave=12)
	frequencies = librosa.cqt_frequencies(84, 32.70, 12)
	weighted_cqts = librosa.perceptual_weighting(numpy.abs(cqts)**2, frequencies, ref=1.0)

	total_db = 10 * numpy.log10((10 ** (weighted_cqts / 10)).sum(axis=0))

	return {
		'volume.decibals': total_db.astype(numpy.float32),
		'volume.rate': sample_rate / (2**6)
	}
