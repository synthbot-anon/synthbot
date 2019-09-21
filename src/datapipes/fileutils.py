import io
import os
import tarfile
import time

import librosa #type: ignore
import soundfile #type: ignore
from praatio import tgio #type: ignore

import datapipes


NORMALIZED_AUDIO_SAMPLE_RATE = 16000

class VerifiedFile:
	def __init__(self, path: str, exists: bool = False):
		assert not os.path.isdir(path), \
			'file [{}] must not be a directory'.format(path)
		assert (not exists) or os.path.exists(path), \
			'missing file [{}]'.format(path)
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
	path = os.path.normpath(path)
	
	assert os.path.exists(path), \
		'missing file or directory {}'.format(path)

	if os.path.isfile(path):
		return os.path.dirname(path)
	
	return path

def get_name(path: str):
	path = os.path.normpath(path)
	return os.path.basename(path)

class NormalizedAudio(VerifiedFile):
	def __init__(self, input_file: VerifiedFile):
		if datapipes.__dry_run__:
			self.data, self.sample_rate = [], 0
			self.duration = 0
			return

		self.data, self.sample_rate = librosa.load(input_file.path,
			sr=NORMALIZED_AUDIO_SAMPLE_RATE)
		self.duration = len(self.data) / float(NORMALIZED_AUDIO_SAMPLE_RATE)

def read_normalized_transcript(transcript_file: VerifiedFile):
	with open(transcript_file.path) as transcript_fd:
		transcript = transcript_fd.read().strip()
		assert '\n' not in transcript and '\t' not in transcript, \
			'Please remove the newlines and tabs in transcript for [{}]'.format(
				transcript_file.path)
		return transcript

def normalize_path(path: str):
	return path.replace(' ', '-').replace('/', '_')

def write_normalized_audio(input: NormalizedAudio, output_path: str):
	soundfile.write(output_path, input.data, input.sample_rate)

def write_normalized_transcript(transcript: str, audio: NormalizedAudio, output_path: str):
	assert ' ' not in output_path, \
		'Please remove spaces from output path for {}'.format(output_path)
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

class LocalFiles:
	def __init__(self, folder: str):
		self.folder = VerifiedDirectory(folder)

	def get_files(self):
		matching_paths = []
		for root, dirs, files in os.walk(self.folder.path, followlinks=False):
			matching_paths.extend([os.path.join(root, x)
				for x in files if self._accept_path(x)])

		for path in matching_paths:
			try:
				yield self._wrap_path(path)
			except AssertionError as e:
				if not datapipes.__dry_run__:
					raise
				print(str(e))

	def _accept_path(self, path: str):
		raise NotImplementedError

	def _wrap_path(self, path: str):
		return path

def write_tardata(output: tarfile.TarFile, name: str, data: bytes):
	tarinfo = tarfile.TarInfo()
	tarinfo.name = name
	tarinfo.size = len(data)
	tarinfo.mtime = time.time()
	tarinfo.mode = int('644', base=8)

	output.addfile(tarinfo, io.BytesIO(data))
