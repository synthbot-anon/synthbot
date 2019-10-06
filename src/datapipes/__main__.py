import os
import argparse

import datapipes
from datapipes import clipper_in, mfa_out, mfa_in, tar_out
from datapipes.fileutils import *


def generate_mfa_inputs(clips_dir, output_dir):
	aligner = mfa_out.MFAPreprocessor(clips_dir, output_dir)

	for clip in clipper_in.ClipperDataset(clips_dir).get_files():
		try:
			audio_file = VerifiedFile(clip.audio_path, exists=True)

			aligner.generate_result(
				clip.label['character'], 
				audio_file, 
				clip.reference,
				clip.label['transcript'])
		except AssertionError as e:
			if not datapipes.__dry_run__:
				raise
			print(e)

	if datapipes.__dry_run__ or datapipes.__verbose__:
		print('Done')

def generate_audio_tar(clips_dir, alignments_dir, output_dir, 
		audio_format, sample_rate):
	with tar_out.TarGenerator(output_dir, audio_format, sample_rate) as tar_generator:
		known_audio_files = {}
		
		if datapipes.__verbose__:
			print('reading utterances from ', clips_dir)

		for clip in clipper_in.ClipperDataset(clips_dir).get_files():
			known_audio_files[clip.reference] = clip

		if datapipes.__verbose__:
			print('writing output files to', output_dir)

		for alignments in mfa_in.MFADataset(alignments_dir).get_files():
			try:
				reference = alignments.reference
				audio = known_audio_files[reference]

				tar_generator.generate_result(reference, audio, alignments)
			except AssertionError as e:
				if not datapipes.__dry_run__:
					raise
				print(e)

	if datapipes.__dry_run__ or datapipes.__verbose__:
		print('Done')

def add_common_args(parser):
	parser.add_argument('--verbose', required=False, action='store_true',
			help='print status while processing files')
	parser.add_argument('--dry-run', required=False, action='store_true',
		help='output only errors that will be encountered when processing')
	parser.add_argument('--delta', required=False, action='store_true',
		help='process only new files')

def process_common_args(args):
	datapipes.__verbose__ = args.verbose
	datapipes.__dry_run__ = args.dry_run
	datapipes.__delta__ = args.delta

if __name__ == '__main__':
	# Basic structure:
	#	* Parse arguments once to figure out what function F to perform.
	# 	* Parse arguments a second time to figure out what the arguments 
	# 	  are for function F.
	# 	* Pass arguments to a method designed to execute F. 
	#
	# The main method handles parsing arguments from the command line so
	# it's easy to spot inconsistencies across all functions. Each
	# specialized method process arguments semantically so we can focus
	# on writing just utility functions in other files.
	
	parser = argparse.ArgumentParser(
		description='Preprocessing helper functions for synthbot.')
	group = parser.add_mutually_exclusive_group(required=True)
	group.add_argument('--mfa-inputs', required=False, action='store_true')
	group.add_argument('--audio-tar', required=False, action='store_true')

	args = parser.parse_known_args()[0]
	if args.mfa_inputs:
		mfa_parser = argparse.ArgumentParser(
			description='Convert transcript text files to start-end-utterance tsv format.')
		mfa_parser.add_argument('--mfa-inputs', required=True, action='store_true')
		add_common_args(mfa_parser)
		
		mfa_parser.add_argument('--input', metavar='fn', type=str, required=True,
			help="input folder holding Clipper's clips")
		mfa_parser.add_argument('--output', metavar='fn', type=str, required=True,
			help='output folder that will hold inputs suitable for MFA')
	
		args = mfa_parser.parse_args()
		process_common_args(args)
		generate_mfa_inputs(args.input, args.output)
	
	elif args.audio_tar:
		tfds_parser = argparse.ArgumentParser(
			description='Create tensorflow dataset from audio clips and textgrids')
		tfds_parser.add_argument('--audio-tar', required=True, action='store_true')
		add_common_args(tfds_parser)

		tfds_parser.add_argument('--input-audio', metavar='fn', type=str, required=True,
			help="input folder holding Clipper's clips")
		tfds_parser.add_argument('--input-alignments', metavar='fn', type=str, required=True,
			help="input folder holding MFA-generated textgrid alignments")
		tfds_parser.add_argument('--output', metavar='fn', type=str, required=True,
			help='output folder for tensorflow dataset files')
		tfds_parser.add_argument('--audio-format', metavar='fmt', type=str, required=True,
			help='file format for audio files')
		tfds_parser.add_argument('--sampling-rate', metavar='sr', type=int, required=True,
			help='sampling rate for audio files')

		args = tfds_parser.parse_args()
		process_common_args(args)
		generate_audio_tar(args.input_audio, args.input_alignments, 
			args.output, args.audio_format, args.sampling_rate)
