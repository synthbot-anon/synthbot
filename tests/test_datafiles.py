import glob
import os
import pytest

import librosa

from ponysynth.corpus import ClipperArchive, InfoArchive, phoneme_transcription
from datapipes.fileutils import get_name

ARCHIVE_PATHS = '/home/celestia/data/audio-tar/*'
SAMPLE_RATE = 48000

EXTRA_PATHS = '/home/celestia/data/audio-info/*'

COOKIE_PATHS = '/home/celestia/data/audio-trimmed-22khz/*'
COOKIE_RATE = 22050

OOV_PATHS = '/home/celestia/data/mfa-alignments/*/oovs_found.txt'
ALIGNMENT_PATHS = '/home/celestia/data/mfa-alignments/*'


@pytest.fixture
def archives():
    return load_archives(glob.glob(ARCHIVE_PATHS))


@pytest.fixture
def extras():
    return load_extras(glob.glob(EXTRA_PATHS))


@pytest.fixture
def cookie_archives():
    return load_archives(glob.glob(COOKIE_PATHS))


def load_archives(paths):
    result = {}
    for path in paths:
        filename = get_name(path)
        character, ext = os.path.splitext(filename)

        assert ext == '.tar'
        result[character] = ClipperArchive(path)

    return result


def load_extras(paths):
    result = {}
    for path in paths:
        filename = get_name(path)
        character, ext = os.path.splitext(filename)

        assert ext == '.txz'
        result[character] = InfoArchive(path)

    return result


def test_archives(archives):
    for archive in archives.values():
        assert_valid_archive(archive)
        assert_valid_audio(archive, SAMPLE_RATE)


def test_cookie_clips(cookie_archives):
    for archive in cookie_archives.values():
        assert_valid_archive(archive)
        assert_valid_audio(archive, COOKIE_RATE)


def assert_valid_archive(archive):
    for key, label in archive.labels():
        assert_valid_label(key, label)
    assert key != None


def assert_valid_label(key, label):
    assert_phone_sequence(label)
    assert_word_sequence(label)
    assert_valid_tags(label)
    assert_valid_transcript(label)


def assert_phone_sequence(label):
    # make sure the phoneme sequences form a chain from start to end
    assert label['phones'][0]['interval'][0] == 0
    for pre, post in zip(label['phones'][:-1], label['phones'][1:]):
        assert pre['interval'][1] == post['interval'][0]


def assert_word_sequence(label):
    # make sure the word sequences form a chain from start to end
    assert label['words'][0]['interval'][0] >= 0
    for pre, post in zip(label['words'][:-1], label['words'][1:]):
        assert pre['interval'][1] <= post['interval'][0]


def assert_valid_tags(label):
    for tag in label['tags']:
        capitalized = ' '.join(x.capitalize() for x in tag.split())
        assert tag == capitalized


def assert_valid_transcript(label):
    assert label['utterance']['content'] != ''


def assert_valid_audio(archive, expected_rate):
    for key, audio in archive.audio():
        samples, rate = librosa.core.load(audio, sr=None)
        assert rate == expected_rate
        assert len(samples) > rate * 0.15, \
         f'found a very short clip: {key}'


def test_phoneme_transcriptions(archives):
    for archive in archives.values():
        for key, label in archive.labels():
            transcription = phoneme_transcription(label)
            assert '{' in transcription and '}' in transcription
            assert '{}' not in transcription


def test_extras(archives, extras):
    extra_keys = set()

    for extra in extras.values():
        assert_valid_extra(extra)
        extra_keys.update(extra.keys())

    for archive in archives.values():
        for key in archive.keys():
            assert key in extra_keys


def assert_valid_extra(extra):
    for key, info in extra.info():
        assert 'formants' in info
        assert 'pitch' in info
        assert 'intensity' in info
        assert 'gci.sec' in info
        assert len(info['intensity']) > 0

    assert key != None


def test_oovs():
    oov_paths = glob.glob(OOV_PATHS)
    for path in oov_paths:
        assert open(path).read() == ''


def test_alignments():
    alignment_paths = glob.glob(ALIGNMENT_PATHS)
    for path in alignment_paths:
        entries = os.scandir(path)
        assert next(entries)
