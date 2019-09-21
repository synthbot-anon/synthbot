import io
import json
import os
import tarfile
import time

from datapipes.fileutils import *
from datapipes import clipper_in, mfa_in


class TFDSGenerator:
	def __init__(self, output_dir):
		self.output_dir = VerifiedDirectory(output_dir).path
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

	def get_output_audio_path(self, reference, audio_path):
		extension = os.path.splitext(audio_path)[-1]
		return os.path.join(reference, 'audio{}'.format(extension))

	def get_output_label_path(self, reference):
		return os.path.join(reference, 'label.json')
	
	def generate_result(self, reference: str, 
			audio: clipper_in.ClipperFile, alignments: mfa_in.MFAAlignmentsFile):
		assert reference == audio.reference
		assert reference == alignments.reference

		audio_file = VerifiedFile(audio.audio_path)
		
		assert normalize_path(audio.label['character']) == alignments.character
		character = alignments.character

		output_audio_path = self.get_output_audio_path(reference, audio_file.path)
		output_label_path = self.get_output_label_path(reference)

		label = {
			'character': character,
			'episode': audio.episode,
			'tags': audio.label['tags'],
			'noise': audio.label['noise'],
			'utterance': {
				'content': audio.label['transcript'],
				'episode_interval': [
					audio.label['start'], audio.label['end']]
			},
			'words': alignments.words,
			'phones': alignments.phones
		}
		
		output_file = self.get_character_tgz(character)
		label_data = json.dumps(label).encode('utf-8')

		if datapipes.__dry_run__:
			return

		output_file.add(audio_file.path, arcname=output_audio_path)
		write_tardata(output_file, output_label_path, label_data)

	def close_all(self):
		for tgz in self.character_handles.values():
			tgz.close()

	def __enter__(self):
		return self

	def __exit__(self, type, value, traceback):
		self.close_all()
