
import librosa, soundfile # type: ignore
import os
from datapipes.verifiedfiles import *
import datapipes


class MFAPreprocessor:
	def __init__(self, input_path: str, output_dir: VerifiedDirectory):
		self.input_dir = get_directory(input_path)
		self.output_dir = output_dir.path

		if datapipes.__delta__:
			# get known output files
			self.known_audio_paths = set()
			self.known_transcript_paths = set()
			for root, dirs, files in os.walk(self.output_dir, followlinks=False):
				self.known_audio_paths.update([os.path.join(root, x)
					for x in files if os.path.splitext(x)[-1] == OUTPUT_AUDIO_FORMAT])
				self.known_transcript_paths.update([os.path.join(root, x)
					for x in files if os.path.splitext(x)[-1] == OUTPUT_TRANSCRIPT_FORMAT])

	def get_character_path(self, character):
		normalized_character = path_to_normalized_path(character)
		character_path = os.path.join(self.output_dir, normalized_character)
		verified_path = VerifiedDirectory(character_path)
		return verified_path.path

	def get_output_path(self, character, input_path):
		relative_input_path = os.path.relpath(input_path, self.input_dir)
		relative_output_path = path_to_normalized_path(relative_input_path)
		
		return os.path.join(self.get_character_path(character), relative_output_path)

	def generate_input(self, character: str, audio_file: VerifiedFile, transcript_file: VerifiedFile):
		base_filename = os.path.splitext(audio_file.path)[0]

		output_transcript_path = self.get_output_path(character,
			'{}{}'.format(base_filename, OUTPUT_TRANSCRIPT_FORMAT))
		output_audio_path = self.get_output_path(character, 
			'{}{}'.format(base_filename, OUTPUT_AUDIO_FORMAT))

		if datapipes.__delta__:
			if output_transcript_path in self.known_transcript_paths \
					and output_audio_path in self.known_audio_paths:
				if datapipes.__verbose__:
					print('skipping {}'.format(audio_file.path))
				return

		if datapipes.__dry_run__:
			return

		input_audio = NormalizedAudio(audio_file)
		input_transcript = read_normalized_transcript(transcript_file)
		
		write_normalized_transcript(input_transcript, input_audio, output_transcript_path)
		write_normalized_audio(input_audio, output_audio_path)

