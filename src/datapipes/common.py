import itertools
import json
import os


class Dataset(object):
    def __init__(self, generator):
        self.generator = generator


class Transform(object):
    def __init__(self, fn):
        self.fn = fn


class Package(object):
    pass


class Unpacker(object):
    def __init__(self):
        pass


def filePaths(path):
    for root, dirs, files in os.walk(path, followlinks=False):
        for filename in files:
            yield os.path.join(root, filename)


def fileLines(path):
    with open(path) as contents:
        for line in contents:
            yield line


def fileJson(path):
    with open(path) as contents:
        return json.loads(contents.read())


def parse_parent_name(path: str):
    return parse_name(os.path.dirname(path))


def parse_name(path: str):
    path = os.path.normpath(path)
    base = os.path.basename(path)
    return os.path.splitext(base)[0]


def parse_parent_path(path: str):
    return os.path.dirname(path)
