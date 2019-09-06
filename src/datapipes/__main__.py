import argparse
from datapipes import clipper_in, mfa_out
from datapipes.verifiedfiles import *
import datapipes

if __name__ == '__main__':
	parser = argparse.ArgumentParser(
		description='Convert transcript text files to start-end-utterance tsv format.')
	parser.add_argument('--input', metavar='fn', type=str, required=True,
		help='input file (depth=0) or folder (depth=1)')
	parser.add_argument('--output', metavar='fn', type=str, required=True,
		help='output file or folder')
	parser.add_argument('--dry-run', required=False, action='store_true',
		help='output only errors that will be encountered when processing')
	parser.add_argument('--delta', required=False, action='store_true',
		help='process only new files')
	parser.add_argument('--verbose', required=False, action='store_true',
		help='print status while processing files')
	args = parser.parse_args()

	datapipes.__dry_run__ = args.dry_run
	datapipes.__verbose__ = args.verbose
	datapipes.__delta__ = args.delta

	# TODO: load transcript in aligner, not clipper
	aligner = mfa_out.MFAPreprocessor(args.input, VerifiedDirectory(args.output))
	clipper = clipper_in.ClipperDataset(VerifiedDirectory(args.input))

	for clip in clipper.get_clips():
		try:
			audio_file = VerifiedFile(clip.audio_path)
			transcript_file = VerifiedFile(clip.transcript_path)
			aligner.generate_input(clip.character, audio_file, transcript_file)
		except AssertionError as e:
			if not datapipes.__dry_run__:
				raise
			print(e)
