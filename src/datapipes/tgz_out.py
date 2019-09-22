import io
import json
import os
import tarfile
import time
import librosa
import soundfile

from datapipes.fileutils import *
from datapipes import clipper_in, mfa_in


class TgzGenerator:
	def __init__(self, output_dir, audio_format, sample_rate):
		self.output_dir = VerifiedDirectory(output_dir).path
		self.audio_format = audio_format
		self.sample_rate = sample_rate
		self.character_handles = {}
	
	def get_character_tgz(self, character):
		if character in self.character_handles:
			return self.character_handles[character]

		normalized_character = normalize_path(character)
		character_tgz_path = os.path.join(self.output_dir,
			'{}.tgz'.format(normalized_character))
		
		result = tarfile.open(character_tgz_path, 'w:gz')
		self.character_handles[character] = result

		return result

	def generate_result(self, reference: str, 
			audio: clipper_in.ClipperFile, alignments: mfa_in.MFAAlignmentsFile):
		assert reference == audio.reference
		assert reference == alignments.reference

		audio_file = VerifiedFile(audio.audio_path)
		
		assert normalize_path(audio.label['character']) == alignments.character
		character = alignments.character

		output_audio_path = os.path.join(reference, 'audio.{}'.format(self.audio_format))
		output_label_path = os.path.join(reference, 'label.json')

		label = {
			'character': character,
			'episode': audio.episode,
			'tags': audio.label['tags'],
			'noise': audio.label['noise'],
			'utterance': {
				'content': audio.label['transcript'],
				'episode_interval': [
					float(audio.label['start']), float(audio.label['end'])]
			},
			'words': alignments.words,
			'phones': alignments.phones
		}
		
		output_file = self.get_character_tgz(character)
		label_data = json.dumps(label).encode('utf-8')

		if datapipes.__dry_run__:
			return

		input_audio, _ = librosa.load(audio_file.path, sr=self.sample_rate)
		output_audio = io.BytesIO()
		soundfile.write(output_audio, input_audio, 
			self.sample_rate, format=self.audio_format)

		write_tardata(output_file, output_audio_path, output_audio.getvalue())
		write_tardata(output_file, output_label_path, label_data)

	def close_all(self):
		for tgz in self.character_handles.values():
			tgz.close()

	def __enter__(self):
		return self

	def __exit__(self, type, value, traceback):
		self.close_all()
