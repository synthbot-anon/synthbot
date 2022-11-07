import dataclasses
import itertools
import json
import os
import tempfile
import tqdm


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
    path = os.path.normpath(path)
    return os.path.dirname(path)


class VerboseLogger:
    def tqdm(self, *args, **kwargs):
        return tqdm.tqdm(*args, **kwargs)

    def print(self, *args, **kwargs):
        print(*args, **kwargs)


class _TqdmNoop:
    def __init__(self, iterable=None, **kwargs):
        self.iterable = iterable

    def __iter__(self):
        return iter(self.iterable)


class NoopLogger:
    def tqdm(self, *args, **kwargs):
        return _TqdmNoop(*args, **kwargs)

    def print(self, *args, **kwargs):
        pass


def logger(verbose):
    if verbose:
        return VerboseLogger()
    else:
        return NoopLogger()

class TemporaryDirectory:
    def __init__(self, suffix=None, prefix=None, dir=None):
        self.tmpdir = tempfile.TemporaryDirectory(suffix, prefix, dir)
        self.path = self.tmpdir.name
        self.is_open = False

    def __enter__(self):
        self.is_open = True
        self.tmpdir.__enter__()
        return self

    def __exit__(self, *exc):
        self.is_open = False
        return self.tmpdir.__exit__(*exc)

    def subdir(self, name):
        if not self.is_open:
            raise Exception('call this function within a TemporaryDirectory context (with)')

        path = os.path.join(self.path, name)
        os.makedirs(path, exist_ok=True)
        return path
