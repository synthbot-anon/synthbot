import os

import librosa #type: ignore
import soundfile #type: ignore
from praatio import tgio #type: ignore

import datapipes


AUDIO_SAMPLE_RATE = 16000
OUTPUT_AUDIO_FORMAT = '.wav'
OUTPUT_TRANSCRIPT_FORMAT = '.textgrid'

class VerifiedFile:
	def __init__(self, path: str):
		assert not os.path.isdir(path), \
			'file [{}] must not be a directory'.format(path)
		self.path = os.path.abspath(path)

class VerifiedDirectory:
	def __init__(self, path: str):
		if os.path.exists(path):
			assert os.path.isdir(path), \
				'Output file {} must be a directory'.format(path)
		else:
			os.makedirs(path)

		self.path = path

def get_directory(path: str):
	if os.path.isfile(path):
		return os.path.dirname(path)
	else:
		return path

class NormalizedAudio(VerifiedFile):
	def __init__(self, input_file: VerifiedFile):
		if datapipes.__dry_run__:
			self.data, self.sample_rate = [], 0
			self.duration = 0
			return

		self.data, self.sample_rate = librosa.load(input_file.path, sr=AUDIO_SAMPLE_RATE)
		self.duration = len(self.data) / float(AUDIO_SAMPLE_RATE)

def read_normalized_transcript(transcript_file: VerifiedFile):
	with open(transcript_file.path) as transcript_fd:
		transcript = transcript_fd.read().strip()
		assert '\n' not in transcript and '\t' not in transcript, \
			'Please remove the newlines and tabs in transcript for [{}]'.format(
				transcript_file.path)
		return transcript

def path_to_normalized_path(path: str):
	return path.replace(' ', '-').replace('/', '_')

def write_normalized_audio(input: NormalizedAudio, output_path: str):
	if datapipes.__verbose__:
		print('writing normalized audio to {}'.format(output_path))
	soundfile.write(output_path, input.data, input.sample_rate)

def write_normalized_transcript(transcript: str, audio: NormalizedAudio, output_path: str):
	assert '\n' not in transcript and '\t' not in transcript, \
			'Please remove the newlines and tabs in transcript for [{}]'.format(
				transcript)

	if datapipes.__verbose__:
		print('writing normalized transcript to {}'.format(output_path))

	duration = audio.duration
	textgrid = tgio.Textgrid()
	utterance = tgio.IntervalTier('utt', [], 0, duration)
	utterance.insertEntry(tgio.Interval(start=0, end=duration, label=transcript))
	textgrid.addTier(utterance)

	textgrid.save(output_path, useShortForm=False)
