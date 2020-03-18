import os
import re

import librosa, soundfile  # type: ignore

import datapipes
from datapipes.fileutils import *

OUTPUT_AUDIO_FORMAT = '.wav'
OUTPUT_TRANSCRIPT_FORMAT = '.textgrid'


def normalize_transcript(text):
    # REQ: This MUST be kept in sync with
    # ponysynth.corpus.phoneme_transcription.

    result = re.sub(r'[.?!,;"]', ' ', text)
    result = result.replace('-', '').replace("'", '')
    return result


class MFAPreprocessor:
    def __init__(self, input_path: str, output_dir: str):
        self.input_dir = get_directory(input_path)
        self.output_dir = VerifiedDirectory(output_dir).path

        if datapipes.__delta__:
            # get known output files
            self.known_audio_paths = set()
            self.known_transcript_paths = set()
            for root, dirs, files in os.walk(self.output_dir,
                                             followlinks=False):
                self.known_audio_paths.update([
                    os.path.join(root, x) for x in files
                    if os.path.splitext(x)[-1] == OUTPUT_AUDIO_FORMAT
                ])
                self.known_transcript_paths.update([
                    os.path.join(root, x) for x in files
                    if os.path.splitext(x)[-1] == OUTPUT_TRANSCRIPT_FORMAT
                ])

    def get_character_path(self, character):
        normalized_character = normalize_path(character)
        character_path = os.path.join(self.output_dir, normalized_character)
        verified_path = VerifiedDirectory(character_path)
        return verified_path.path

    def get_output_path(self, character, input_fn):
        output_fn = normalize_path(input_fn)
        return os.path.join(self.get_character_path(character), output_fn)

    def generate_result(self, character: str, audio_file: VerifiedFile,
                        reference: str, transcript: str):

        output_transcript_path = self.get_output_path(
            character, '{}{}'.format(reference, OUTPUT_TRANSCRIPT_FORMAT))
        output_audio_path = self.get_output_path(
            character, '{}{}'.format(reference, OUTPUT_AUDIO_FORMAT))

        if datapipes.__delta__:
            if output_transcript_path in self.known_transcript_paths \
              and output_audio_path in self.known_audio_paths:
                if datapipes.__verbose__:
                    print('skipping {}'.format(audio_file.path))
                return

        if datapipes.__dry_run__:
            return

        input_audio = NormalizedAudio(audio_file)

        # Montreal Forced Aligner is picky about transcriptions
        transcript = normalize_transcript(transcript)

        write_normalized_transcript(transcript, input_audio,
                                    output_transcript_path)
        write_normalized_audio(input_audio, output_audio_path)
