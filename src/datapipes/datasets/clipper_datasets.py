""" """

import dataclasses
import os
from typing import Dict, Set

import datapipes.common
import datapipes.clipper
from datapipes.datasets import clipper_mlp_values
from datapipes.datasets import clipper_other_values


class ClipperParamsHelper(datapipes.clipper.ClipperParams):
    _rootdir: str
    _rootlen: int
    known_characters: Dict
    known_tags: Dict
    known_noise_levels: Dict
    known_sources: Dict
    unknown_characters: Set = set()
    unknown_tags: Set = set()
    unknown_noise_levels: Set = set()
    unknown_sources: Set = set()

    def __init__(
        self, clipper_root, characters=None, tags=None, noise_levels=None, sources=None
    ):
        self.rootdir = clipper_root
        self.known_characters = characters or {}
        self.known_tags = tags or {}
        self.known_noise_levels = noise_levels or {}
        self.known_sources = sources or {}

    @property
    def rootdir(self) -> str:
        return self._rootdir

    @rootdir.setter
    def rootdir(self, value: str):
        self._rootdir = os.path.normpath(value)
        self._rootlen = len(self._rootdir)

    def relpath(self, filepath: str):
        normpath = os.path.normpath(filepath)

        if not normpath.startswith(self.rootdir):
            raise ValueError(
                'cannot take the relative path of "{}" since it is not under "{}"'.format(
                    normpath, self.rootdir
                )
            )

        if normpath == self.rootdir:
            return ""

        return normpath[self._rootlen + 1 :]

    def characters(self, candidate, path):
        if candidate in self.known_characters:
            return self.known_characters[candidate]

        if candidate not in self.unknown_characters:
            print("unknown character", candidate)
            self.unknown_characters.add(candidate)

        # default result
        return candidate

    def tags(self, candidate, path):
        if candidate in self.known_tags:
            return self.known_tags[candidate]

        if candidate not in self.unknown_tags:
            print("unknown tag", candidate)
            self.unknown_tags.add(candidate)

        # default result
        return candidate

    def noise_levels(self, candidate, path):
        if candidate in self.known_noise_levels:
            return self.known_noise_levels[candidate]

        if candidate not in self.unknown_noise_levels:
            print("unknown noise level", candidate)
            self.unknown_noise_levels.add(candidate)

        # default result
        return candidate

    def sources(self, candidate, path):
        candidate = self.relpath(candidate)

        if candidate in self.known_sources:
            return self.known_sources[candidate]

        if candidate not in self.unknown_sources:
            print("unknown source", candidate, "for", path)
            self.unknown_sources.add(candidate)

        # default result
        return candidate


class MlpDialogueParams(ClipperParamsHelper):
    def __init__(self, clipper_root):
        super(MlpDialogueParams, self).__init__(
            clipper_root,
            characters=clipper_mlp_values.CHARACTERS,
            tags=clipper_mlp_values.TAGS,
            noise_levels=clipper_mlp_values.NOISE,
        )

    def sources(self, candidate, path):
        relpath = self.relpath(candidate)

        if relpath.endswith("labels.txt"):
            relpath = os.path.dirname(relpath)

        if relpath in clipper_mlp_values.SOURCES:
            return clipper_mlp_values.SOURCES[relpath]

        if candidate not in self.unknown_sources:
            print("unknown source", candidate, "for", path)
            self.unknown_sources.add(candidate)

        # default result
        return candidate


def mlp_dialogue_dataset(clipper_root):
    params = MlpDialogueParams(clipper_root)
    dataset = datapipes.clipper.ClipperSet(params)

    for entry in os.scandir(f"{clipper_root}/Reviewed episodes"):
        if not entry.is_file():
            print(f"Unexpected directory: Reviewed episodes/{entry.name}")
            continue
        dataset.load_ponysorter(entry.path)

    clip_directories = [
        f"{clipper_root}/Sliced Dialogue/EQG",
        f"{clipper_root}/Sliced Dialogue/FiM",
        f"{clipper_root}/Sliced Dialogue/MLP Movie",
        f"{clipper_root}/Sliced Dialogue/Special source",
        f"{clipper_root}/Sliced Dialogue/Other/Mobile game",
    ]

    for clip_directory in clip_directories:
        print("loading", clip_directory)
        for root, dirs, files in os.walk(clip_directory):
            for filename in files:
                if filename == "labels.txt":
                    continue

                if filename.endswith(".txt"):
                    dataset.load_transcript(f"{root}/{filename}")
                elif filename.endswith(".flac"):
                    dataset.load_audio(f"{root}/{filename}")
                else:
                    print(f"Unexpected file: {root}/{filename}")

    for entry in os.scandir(f"{clipper_root}/Sliced Dialogue/Label files"):
        if not entry.is_file():
            continue
        if entry.name == "songs.txt":
            continue
        if not entry.name.endswith(".txt"):
            continue
            
        dataset.load_audacity(entry.path)

    dataset.load_audacity(f"{clipper_root}/Sliced Dialogue/MLP Movie/labels.txt")

    return dataset


class MlpSongParams(ClipperParamsHelper):
    def __init__(self, clipper_root):
        super(MlpSongParams, self).__init__(
            clipper_root,
            characters=clipper_mlp_values.CHARACTERS,
            tags=clipper_mlp_values.TAGS,
            noise_levels=clipper_mlp_values.NOISE,
            sources={
                "Sliced Dialogue/Songs": "fim:songs",
                "Sliced Dialogue/Label files/songs.txt": "fim:songs",
            },
        )


def mlp_song_dataset(clipper_root):
    params = MlpSongParams(clipper_root)
    dataset = datapipes.clipper.ClipperSet(params)

    for entry in os.scandir(f"{clipper_root}/Sliced Dialogue/Songs/"):
        if not entry.is_file():
            print(f"Unexpected directory: Sliced Dialogue/Songs/{entry.name}")
            continue

        if entry.name.endswith(".txt"):
            dataset.load_transcript(entry.path)
        elif entry.name.endswith(".flac"):
            dataset.load_audio(entry.path)
        else:
            print(f"Unexpected file: Sliced Dialogue/Songs/{entry.name}")

    dataset.load_audacity(f"{clipper_root}/Sliced Dialogue/Label files/songs.txt")

    return dataset


def mlp_sfx_params():
    # todo: convert m4a to flac
    # todo: restructure sfx sounds
    # ... source (e.g., Hoers, Rain, character) / Tag number.flac

    # todo: allow manually adding tags/records to a clipperset
    # maybe post_audio vs put_audio
    pass


class ExtraDialogueParams(ClipperParamsHelper):
    def __init__(self, clipper_root):
        super(ExtraDialogueParams, self).__init__(
            clipper_root,
            characters=clipper_other_values.CHARACTERS,
            tags=clipper_other_values.TAGS,
            noise_levels=clipper_other_values.NOISE,
            sources=clipper_other_values.SOURCES,
        )


def extra_dialogue_dataset(clipper_root):
    params = ExtraDialogueParams(clipper_root)
    dataset = datapipes.clipper.ClipperSet(params)

    clip_directories = [
        f"{clipper_root}/Sliced Dialogue/Other/A Little Bit Wicked (Kristin Chenoworth, Skystar)",
        f"{clipper_root}/Sliced Dialogue/Other/ATHF",
        f"{clipper_root}/Sliced Dialogue/Other/CGP Grey",
        f"{clipper_root}/Sliced Dialogue/Other/Dan vs",
        f"{clipper_root}/Sliced Dialogue/Other/Dr. Who",
        f"{clipper_root}/Sliced Dialogue/Other/Eli, Elite Dangerous (John de Lancie, Discord)",
        f"{clipper_root}/Sliced Dialogue/Other/Star Trek (John de Lancie, Discord)",
        f"{clipper_root}/Sliced Dialogue/Other/Sum - Tales From the Afterlives (Emily Blunt, Tempest)/Sum - Tales From the Afterlives (44.1 kHz)",
        f"{clipper_root}/Sliced Dialogue/Other/TFH/",
    ]

    for clip_directory in clip_directories:
        for root, _, files in os.walk(clip_directory):
            for filename in files:
                if filename in (
                    "Converted.txt",
                    "Converted (1).txt",
                    "Note on these Discord lines.txt",
                ):
                    continue

                if filename.endswith(".txt"):
                    dataset.load_transcript(f"{root}/{filename}")
                elif filename.endswith(".flac"):
                    dataset.load_audio(f"{root}/{filename}")
                else:
                    print(f"Unexpected file: {root}/{filename}")

    for root, _, files in os.walk(f"{clipper_root}/Sliced Dialogue/Label files/Other"):
        for file in files:
            if not file.endswith(".txt"):
                continue

            filepath = os.path.join(root, file)
            dataset.load_audacity(filepath)

    return dataset
