from typing import Iterable

import datapipes.common
import os
import re
from datapipes import clipper_utils
from collections import namedtuple

import dataclasses
from typing import List, Optional, Dict
import json
import pandas
from tqdm import tqdm


PROCESSORS = {
    "original": "original",
    "izo": "izo",
    "unmix": "unmix",
    "": "original",
}


@dataclasses.dataclass
class PonySorterRecord:
    start: float
    end: float
    character: str
    tags: List[str]
    noise: str
    transcript: str
    processor: str

    def label_reference(self):
        timestamp = coarsen_timestamp(self.start)
        label = "{0:02d}_{1:02d}_{2:02d}_{3}_{4}_{5}_{6}".format(
            timestamp.hour,
            timestamp.minute,
            timestamp.second,
            self.character,
            " ".join(self.tags),
            self.noise,
            self.transcript,
        )

        return _label_reference(label)


class PonySorterFile:
    def __init__(self, filepath, params):
        self.filepath = filepath
        self.params = params

    def records(self):
        with open(self.filepath) as contents:
            file_data = json.loads(contents.read())

            for label_data in file_data["labels"]:
                try:
                    data = clipper_utils.load_ponysorter_data(
                        self.params, self.filepath, label_data
                    )

                    result = PonySorterRecord(**data)
                    result.source_reference = self.source_reference
                    yield result

                except clipper_utils.ParseError as error:
                    print(error.message)

    def source_reference(self):
        normpath = os.path.normpath(self.filepath)
        return self.params.sources(normpath, normpath)

    @classmethod
    def quickCheck(cls, filepath):
        if not filepath.endswith(".json"):
            return False

        if not "Reviewed episodes" in filepath.split(os.path.sep):
            return False

        return True

    @classmethod
    def slowCheck(cls, filepath):
        raise Exception("not implemented")


@dataclasses.dataclass
class AudacityRecord:
    label: str
    start: float
    end: float
    character: str
    tags: List[str]
    noise: str
    transcript: str

    def label_reference(self):
        return _label_reference(self.label)

    def source_reference(self):
        # this gets overwritten with AudacityFile.source_reference
        pass


class AudacityFile(object):
    def __init__(self, filepath, params):
        self.filepath = filepath
        self.params = params

    def records(self):
        with open(self.filepath) as contents:
            for line_data in contents:
                try:
                    data = clipper_utils.load_audacity_data(
                        self.params, line_data.strip(), self.filepath
                    )

                    result = AudacityRecord(**data)
                    result.source_reference = self.source_reference
                    yield result

                except Exception as error:
                    print("Error:", str(error))
                    print("\tfile:", self.filepath)
                    print("\tline:", line_data)

    def source_reference(self):
        normpath = os.path.normpath(self.filepath)
        return self.params.sources(normpath, normpath)

    def processor_reference(self):
        filename = datapipes.common.parse_name(self.filepath)
        candidate = filename.split("_")[-1]

        if candidate not in PROCESSORS:
            return "original"

        return PROCESSORS[candidate]

    @classmethod
    def quickCheck(cls, filepath):
        if not filepath.endswith(".txt"):
            return False

        if not "Label files" in filepath.split(os.path.sep):
            return False

        return True

    @classmethod
    def slowCheck(cls, filepath):
        raise Exception("not implemented")


CoarseTimestamp = namedtuple("CoarseTimestamp", ["hour", "minute", "second"])


def coarsen_timestamp(t):
    seconds = int(t)
    hh = seconds // 3600
    mm = (seconds % 3600) // 60
    ss = seconds % 60

    return CoarseTimestamp(hh, mm, ss)


class AudioFile:
    def __init__(self, filepath, params):
        self.filepath = filepath
        self.params = params

    def source_reference(self):
        normpath = os.path.normpath(self.filepath)
        dirpath = os.path.dirname(normpath)
        return self.params.sources(dirpath, normpath)

    def timestamp_reference(self):
        filename = datapipes.common.parse_name(self.filepath)
        match = re.match(r"^([0-9]+)_([0-9]+)_([0-9]+)_.*$", filename)
        if match:
            return CoarseTimestamp(*match.groups())

    def transcript_reference(self):
        label_reference = self.label_reference()
        match = re.match(r"^(?:[^_]*_){6}(.*)$", label_reference)
        if match:
            return match.group(1)

    def label_reference(self):
        filename = datapipes.common.parse_name(self.filepath)
        return _label_reference(filename)

    def character_reference(self):
        filename = datapipes.common.parse_name(self.filepath)
        match = re.match(r"^([^_]*)_(?:[^_]*_){5}.*$", filename)
        if match:
            return self.params.characters(match.group(1), self.filepath)

    @classmethod
    def quickCheck(cls, filepath):
        if not (filepath.endswith(".wav") or filepath.endswith(".flac")):
            return False
        return True

    @classmethod
    def slowCheck(cls, filepath):
        raise Exception("not implemented")


class TranscriptFile:
    def __init__(self, filepath, params):
        self.filepath = filepath
        self.params = params
        self._transcript = None

    def label_reference(self):
        filename = datapipes.common.parse_name(self.filepath)
        return _label_reference(filename)

    def character_reference(self):
        filename = datapipes.common.parse_name(self.filepath)
        match = re.match(r"^([^_]*)_(?:[^_]*_){5}.*$", filename)
        if match:
            return self.params.characters(match.group(1), self.filepath)

    def audacity_label(self):
        filename = datapipes.common.parse_name(self.filepath)
        prefix = re.search(r"^((?:[^_]*_){6})", filename)

        if not prefix:
            print("invalid label:", filename)

        return f"{prefix.group(0)}{self.transcript()}"

    def source_reference(self):
        normpath = os.path.normpath(self.filepath)
        dirpath = os.path.dirname(normpath)
        return self.params.sources(dirpath, normpath)

    def transcript(self):
        if self._transcript:
            return self._transcript

        with open(self.filepath) as contents:
            self._transcript = contents.read()

        return self._transcript

    @classmethod
    def quickCheck(cls, filepath):
        if datapipes.common.parse_parent_name(filepath) == "Source files":
            return False

        if datapipes.common.parse_name(filepath) == "labels":
            return False

        if not filepath.endswith(".txt"):
            return False

        if not "Sliced Dialogue" in filepath.split(os.path.sep):
            return False

        return True


@dataclasses.dataclass
class ClipperRecord:
    audio: Optional[AudioFile] = dataclasses.field(default=None)
    transcript: Optional[TranscriptFile] = dataclasses.field(default=None)
    ponysorter_record: Optional[PonySorterRecord] = dataclasses.field(default=None)
    audacity_records: Dict[str, AudacityRecord] = dataclasses.field(
        default_factory=dict
    )

    def panda(self):
        fields = {}
        if self.audacity_records:
            record = next(iter(self.audacity_records.values()))
            fields["character"] = record.character
            fields["source"] = record.source_reference()
            fields["start"] = float(record.start)
            fields["end"] = float(record.end)
            fields["tags"] = record.tags
            fields["noise"] = record.noise
            fields["transcript"] = record.transcript.replace("’", "'")

        if self.audio:
            fields["audio_path"] = self.audio.filepath

        return pandas.Series(fields)


ClipperKey = namedtuple("ClipperKey", ["source_reference", "label_reference"])


def _label_reference(label_string):
    without_qm = label_string.replace("?", "_")
    without_suffix = re.match(r"^(.*?)(?:-[0-9]+)?$", without_qm).group(0)
    without_trailing = without_suffix.rstrip(",. ")
    return without_trailing


class ClipperParams:
    def __init__(self, characters, tags, noise_levels, sources):
        self.characters = characters
        self.tags = tags
        self.noise_levels = noise_levels
        self.sources = sources


class ClipperSet:
    """ Load clipper-structured audio files and labels."""

    def __init__(self, params):
        self.params = params
        self.ponysorter_files = []
        self.audacity_files = []
        self.audio_files = []
        self.transcript_files = []

    def load_audacity(self, filepath):
        self.audacity_files.append(AudacityFile(filepath, self.params))

    def load_ponysorter(self, filepath):
        self.ponysorter_files.append(PonySorterFile(filepath, self.params))

    def load_audio(self, filepath):
        self.audio_files.append(AudioFile(filepath, self.params))

    def load_transcript(self, filepath):
        self.transcript_files.append(TranscriptFile(filepath, self.params))

    def pandas(self, verbose=True, all_files=False):
        result = {}
        progress_bar = lambda x, desc: x
        logger = datapipes.common.logger(verbose)

        for audio_file in logger.tqdm(self.audio_files, desc="Scanning audio files"):
            label_reference = audio_file.label_reference()
            source_reference = audio_file.source_reference()

            key = ClipperKey(source_reference, label_reference)

            if key in result:
                print("duplicate audio file:", key)

            result.setdefault(key, ClipperRecord()).audio = audio_file

        for transcript_file in logger.tqdm(
            self.transcript_files, desc="Scanning transcript files"
        ):
            label_reference = transcript_file.label_reference()
            source_reference = transcript_file.source_reference()

            key = ClipperKey(source_reference, label_reference)
            result.setdefault(key, ClipperRecord()).transcript = transcript_file

        for audacity_file in logger.tqdm(
            self.audacity_files, desc="Scanning audacity files"
        ):
            source_reference = audacity_file.source_reference()
            processor_reference = audacity_file.processor_reference()

            for audacity_record in audacity_file.records():
                label_reference = audacity_record.label_reference()

                key = ClipperKey(source_reference, label_reference)
                known_records = result.setdefault(key, ClipperRecord())
                known_records.audacity_records[processor_reference] = audacity_record

        if all_files:
            # NOTE: these are ignored by default because they don't match the audacity
            # files
            for ponysorter_file in logger.tqdm(
                self.ponysorter_files, desc="Scanning ponysorter files"
            ):
                source_reference = ponysorter_file.source_reference()

            for ponysorter_record in ponysorter_file.records():
                label_reference = ponysorter_record.label_reference()

                key = ClipperKey(source_reference, label_reference)
                result.setdefault(
                    key, ClipperRecord()
                ).ponysorter_record = ponysorter_record

        verbose_records = logger.tqdm(result.values(), desc="Creating dataframe")

        def _filter_records():
            for record in verbose_records:
                # ignore incomplete records unless the caller requested all files
                if record.audacity_records and record.audio:
                    yield record
                elif all_files:
                    yield record

        return pandas.DataFrame([x.panda() for x in _filter_records()])

    def debugger(self):
        pass


class ClipperDebugger:
    def __init__(self):
        pass

    def run_tests(self):
        # make sure each audio file has matching transcript file
        # make sure each transcript file has matching audio file
        # make sure each audacity record has matching audio and transcript files
        # make sure all values are valid (done implicitly)
        # make sure all ponysorter files match audacity records
        # make sure there are no duplicates

        # on specific datasets:
        # make sure no expected folder is empty
        # make sure no expected file is empty
        # make sure all tags are used
        pass
