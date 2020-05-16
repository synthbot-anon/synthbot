import json
import re
import os


class ParseError(Exception):
    def __init__(self, message):
        super(ParseError, self).__init__(self, message)
        self.message = message


def load_ponysorter_data(context, path, label_data):
    character_key = label_data["character"]
    character = context.characters(character_key, path)

    # get tags

    # hack because "canterlot voice" is treated as two tags
    if label_data["mood"] == ["canterlot", "voice"]:
        label_data["mood"] = ["canterlot voice"]

    tags = [context.tags(x, path) for x in label_data["mood"]]

    noise_key = label_data["noise_level"]
    noise = context.noise_levels(noise_key, path)

    return {
        "start": label_data["start"],
        "end": label_data["end"],
        "character": character,
        "tags": tags,
        "noise": noise,
        "transcript": label_data["transcript"],
        "processor": label_data["ideal_source"],
    }


def load_audacity_data(context, line_data, path):
    start, end, label = line_data.split("\t")

    label_parts = label.split("_")
    # skip hh_mm_ss
    assert re.match(r"[0-9][0-9]", label_parts[0])
    assert re.match(r"[0-9][0-9]", label_parts[1])
    assert re.match(r"[0-9][0-9]", label_parts[2])

    # get character name
    character_key = label_parts[3]
    character = context.characters(character_key, path)

    # get tags
    if label_parts[4] == "Canterlot Voice":
        tags = context.tags("Canterlot Voice", path)
    else:
        tags = [context.tags(x, path) for x in label_parts[4].split()]

    # noise level
    noise_level = context.noise_levels(label_parts[5], path)

    # get transcript
    transcript = label_parts[6].strip()
    if len(label_parts) != 7:
        raise ParseError("Excess label parts in {}".format(line_data.strip()))

    return {
        "label": label,
        "start": start,
        "end": end,
        "character": character,
        "tags": tags,
        "noise": noise_level,
        "transcript": transcript,
    }
