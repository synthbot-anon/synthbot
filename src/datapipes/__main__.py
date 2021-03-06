import os
import argparse

import datapipes
from datapipes import (clipper_in, mfa_out, mfa_in, audiotar_out,
                       audioinfo_out, audiorecord_out, dictionary_out)
from datapipes.fileutils import *
from ponysynth.corpus import ClipperArchive, InfoArchive


def generate_mfa_inputs(clips_dir, output_dir):
    aligner = mfa_out.MFAPreprocessor(clips_dir, output_dir)

    for clip in clipper_in.ClipperDataset(clips_dir).get_files():
        if clip.reference == None:
            continue

        try:
            audio_file = VerifiedFile(clip.audio_path, exists=True)

            aligner.generate_result(clip.label['character'], audio_file,
                                    clip.reference, clip.label['transcript'])
        except AssertionError as e:
            if not datapipes.__dry_run__:
                raise
            print(e)

    if datapipes.__dry_run__ or datapipes.__verbose__:
        print('Done')


def generate_audio_tar(clips_dir, alignments_dir, output_dir, audio_format,
                       sample_rate):
    with audiotar_out.AudioTarGenerator(output_dir, audio_format,
                                        sample_rate) as tar_generator:
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


def generate_audio_info(archive_fn, output_fn):
    with audioinfo_out.AudioInfoGenerator(output_fn) as tar_generator:
        archive = ClipperArchive(archive_fn)

        for key, audio in archive.audio():
            tar_generator.generate_result(key, audio)

    if datapipes.__dry_run__ or datapipes.__verbose__:
        print('Done')


def generate_labels_record(audio_archive_fn, audio_info_fn, output_fn):
    if datapipes.__verbose__:
        print(f'Generating {output_fn}')

    record_generator = audiorecord_out.LabelRecordGenerator(
        VerifiedFile(output_fn).path)
    audio_archive = ClipperArchive(
        VerifiedFile(audio_archive_fn, exists=True).path)
    info_archive = InfoArchive(VerifiedFile(audio_info_fn, exists=True).path)
    record_generator.generate_result(audio_archive, info_archive)

    if datapipes.__dry_run__ or datapipes.__verbose__:
        print('Done')


def generate_dictionary(include, clipper_path, output_path):
    if datapipes.__verbose__:
        print('Generating dictionaries')

    clipper_files = clipper_in.ClipperDataset(clipper_path).get_files()
    dictionary_generator = dictionary_out.DictionaryGenerator(
        VerifiedDirectory(output_path).path)
    for dictionary in include:
        if datapipes.__verbose__:
            print(f'adding words from {dictionary}')
        dictionary_generator.update(VerifiedFile(dictionary, exists=True).path)

    if datapipes.__verbose__:
        print(f'found {len(dictionary_generator.dictionary)} words')
        print(f'checking {len(clipper_labels)} clips')

    dictionary_generator.check_transcripts(clipper_files)
    dictionary_generator.generate_result()

    if datapipes.__dry_run__ or datapipes.__verbose__:
        print('Done')


def add_common_args(parser):
    parser.add_argument('--verbose',
                        required=False,
                        action='store_true',
                        help='print status while processing files')
    parser.add_argument(
        '--dry-run',
        required=False,
        action='store_true',
        help='output only errors that will be encountered when processing')
    parser.add_argument('--delta',
                        required=False,
                        action='store_true',
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
    group.add_argument('--audio-info', required=False, action='store_true')
    group.add_argument('--labels-tfrecord',
                       required=False,
                       action='store_true')
    group.add_argument('--dictionary', required=False, action='store_true')

    args = parser.parse_known_args()[0]
    if args.mfa_inputs:
        mfa_parser = argparse.ArgumentParser(
            description=
            'Convert transcript text files to start-end-utterance tsv format.')
        mfa_parser.add_argument('--mfa-inputs',
                                required=True,
                                action='store_true')
        add_common_args(mfa_parser)

        mfa_parser.add_argument('--input',
                                metavar='fn',
                                type=str,
                                required=True,
                                help="input folder holding Clipper's clips")
        mfa_parser.add_argument(
            '--output',
            metavar='fn',
            type=str,
            required=True,
            help='output folder that will hold inputs suitable for MFA')

        args = mfa_parser.parse_args()
        process_common_args(args)
        generate_mfa_inputs(args.input, args.output)

    elif args.audio_tar:
        audiotar_parser = argparse.ArgumentParser(
            description='Create an archive file of audio clips and textgrids')
        audiotar_parser.add_argument('--audio-tar',
                                     required=True,
                                     action='store_true')
        add_common_args(audiotar_parser)

        audiotar_parser.add_argument(
            '--input-audio',
            metavar='fn',
            type=str,
            required=True,
            help="input folder holding Clipper's clips")
        audiotar_parser.add_argument(
            '--input-alignments',
            metavar='fn',
            type=str,
            required=True,
            help="input folder holding MFA-generated textgrid alignments")
        audiotar_parser.add_argument('--output',
                                     metavar='fn',
                                     type=str,
                                     required=True,
                                     help='output folder for archive files')
        audiotar_parser.add_argument('--audio-format',
                                     metavar='fmt',
                                     type=str,
                                     required=True,
                                     help='file format for audio files')
        audiotar_parser.add_argument('--sampling-rate',
                                     metavar='sr',
                                     type=int,
                                     required=True,
                                     help='sampling rate for audio files')

        args = audiotar_parser.parse_args()
        process_common_args(args)
        generate_audio_tar(args.input_audio, args.input_alignments,
                           args.output, args.audio_format, args.sampling_rate)

    elif args.audio_info:
        audioinfo_parser = argparse.ArgumentParser(
            description='Create a data dump of utterance information')
        audioinfo_parser.add_argument('--audio-info',
                                      required=True,
                                      action='store_true')
        add_common_args(audioinfo_parser)

        audioinfo_parser.add_argument(
            '--input-tar',
            metavar='fn',
            type=str,
            required=True,
            help="input folder holding a clips (tar)chive file")
        audioinfo_parser.add_argument(
            '--output-txz',
            metavar='fn',
            type=str,
            required=True,
            help='output folder for utterance information')

        args = audioinfo_parser.parse_args()
        process_common_args(args)
        generate_audio_info(args.input_tar, args.output_txz)

    elif args.labels_tfrecord:
        labelsrecord_parser = argparse.ArgumentParser(
            description='Create a tfrecord dump of utterance labels')
        labelsrecord_parser.add_argument('--labels-tfrecord',
                                         required=True,
                                         action='store_true')
        add_common_args(labelsrecord_parser)

        labelsrecord_parser.add_argument(
            '--input-labels',
            metavar='fn',
            type=str,
            required=True,
            help="input folder holding a clips (tar)chive file")
        labelsrecord_parser.add_argument(
            '--input-info',
            metavar='fn',
            type=str,
            required=True,
            help="input folder holding an info (txz) archive file")
        labelsrecord_parser.add_argument(
            '--output-tfrecord',
            metavar='fn',
            type=str,
            required=True,
            help='output filename for record information')

        args = labelsrecord_parser.parse_args()
        process_common_args(args)
        generate_labels_record(args.input_labels, args.input_info,
                               args.output_tfrecord)

    elif args.dictionary:
        dictionary_parser = argparse.ArgumentParser(
            description='Create a merged dictionary')
        dictionary_parser.add_argument('--dictionary',
                                       required=True,
                                       action='store_true')
        add_common_args(dictionary_parser)

        dictionary_parser.add_argument(
            '--include',
            metavar='fn',
            type=str,
            required=True,
            help="dictionary to include in the result",
            nargs='+')
        dictionary_parser.add_argument(
            '--clipper-path',
            metavar='fn',
            type=str,
            required=True,
            help="folder containing clipper samples for completeness checks")
        dictionary_parser.add_argument('--output-path',
                                       metavar='fn',
                                       type=str,
                                       required=True,
                                       help='output path for the dictionary')

        args = dictionary_parser.parse_args()
        process_common_args(args)
        generate_dictionary(args.include, args.clipper_path, args.output_path)
