import itertools
import os
import re
from typing import *
import tarfile
import json
import random
import io

import librosa  # type: ignore
import soundfile
import numpy

from ponysynth.indexes import SubstringIndex


class ClipperArchive:
    def __init__(self, archive_path):
        self._archive = tarfile.open(archive_path, mode='r')
        self._tarobjects = _load_tar_objects(self._archive)

    def read_label(self, key):
        file = self._archive.extractfile(self._tarobjects[key]['label'])
        data = json.loads(file.read().decode('utf-8'))
        data['key'] = key
        return data

    def read_audio(self, key):
        file = self._archive.extractfile(self._tarobjects[key]['audio'])
        return file

    def labels(self):
        for key in self._tarobjects.keys():
            yield key, self.read_label(key)

    def audio(self):
        for key in self._tarobjects.keys():
            yield key, self.read_audio(key)

    def keys(self):
        return self._tarobjects.keys()


class InfoArchive:
    def __init__(self, archive_path):
        self._archive = tarfile.open(archive_path, mode='r:xz')
        self._tarobjects = _load_tar_objects(self._archive)

    def read_info(self, key):
        file = self._archive.extractfile(self._tarobjects[key]['info'])
        data = json.loads(file.read().decode('utf-8'))
        data['key'] = key
        return data

    def info(self):
        for key in self._tarobjects.keys():
            yield key, self.read_info(key)

    def keys(self):
        return self._tarobjects.keys()


class SpeechCorpus:
    def __init__(self, archive_path):
        self.archive = ClipperArchive(archive_path)
        self._phone_idx = None

    def build_phone_index(self, substrIdx=SubstringIndex):
        self._phone_idx = substrIdx()

        for key, label in self.archive.labels():
            phones = [x['content'] for x in label['phones']]
            self._phone_idx.index(phones, label)

    def nphones(self, n):
        assert self._phone_idx != None

        def _gen():
            for utterance, offset in self._phone_idx.read_layer(height=n):
                yield (utterance, offset, 3)

        return PhoneSeqs(self, _gen())

    def phones(self):
        return self.nphones(1)

    def diphones(self):
        return self.nphones(2)

    def triphones(self):
        return self.nphones(3)

    def phoneseqs(self, phonemes):
        def _gen():
            length = len(phonemes)
            for utterance, offset in self._phone_idx.find(phonemes):
                yield (utterance, offset, length)

        return PhoneSeqs(self, _gen())


def _iter_sample_fast(iterable, samplesize):
    """
	From DzinX on https://stackoverflow.com/questions/12581437
	Take random samples from a generator.
	"""
    results = []
    iterator = iter(iterable)
    # Fill in the first samplesize elements:
    try:
        for _ in range(samplesize):
            results.append(next(iterator))
    except StopIteration:
        raise ValueError("Sample larger than population.")
    random.shuffle(results)  # Randomize their positions
    for i, v in enumerate(iterator, samplesize):
        r = random.randint(0, i)
        if r < samplesize:
            results[r] = v  # at a decreasing rate, replace random items
    return (x for x in results)


class PhoneSeqs:
    def __init__(self, corpus, generator):
        self.corpus = corpus
        self.generator = generator

    def sample(self, k=1):
        return PhoneSeqs(self.corpus, _iter_sample_fast(self.generator, k))

    def __iter__(self):
        return (PhoneSeq(self.corpus, *x) for x in self.generator)

    def cache(self):
        return PhoneSeqsCache(self.corpus, list(self.generator))


class PhoneSeqsCache:
    def __init__(self, corpus, cache):
        self.corpus = corpus
        self.cache = cache

    def sample(self, k=1):
        return [
            PhoneSeq(self.corpus, *x) for x in random.sample(self.cache, k=k)
        ]

    def __iter__(self):
        return (PhoneSeq(self.corpus, *x) for x in self.cache)

    def __next__(self):
        return PhoneSeq(self.corpus, *self.cache[0])

    def __getitem__(self, index):
        return PhoneSeq(self.corpus, *self.cache[index])

    def __len__(self):
        return len(self.cache)


class PhoneSeq:
    def __init__(self, corpus, clip, offset, length):
        self.corpus = corpus
        self.clip = clip
        self.offset = offset
        self.length = length

    def _phones(self):
        start = self.offset
        end = self.offset + self.length
        return self.clip['phones'][start:end]

    def intervals(self):
        start = self.offset
        end = self.offset + self.length

        clip_intervals = [x['interval'] for x in self._phones()]
        seq_start = clip_intervals[0][0]
        return numpy.array(clip_intervals) - seq_start

    def phonemes(self):
        return tuple((x['content'] for x in self._phones()))

    def diphonemes(self):
        phonemes = self.phonemes()
        diphonemes = zip(phonemes[:-1], phonemes[1:])

        return tuple(diphonemes)

    def audio(self):
        utterance = self.corpus.archive.read_audio(self.clip['key'])
        samples, rate = librosa.core.load(utterance, sr=None)

        intervals = [x['interval'] for x in self._phones()]
        start, _ = intervals[0]
        _, end = intervals[-1]

        start_idx = int(start * rate)
        end_idx = int(end * rate)
        return samples[start_idx:end_idx], rate

    def utterance(self):
        return PhoneSeq(self.corpus, self.clip, 0, len(self.clip['phones']))


def _load_tar_objects(archive):
    result = {}

    for item in archive:
        filename = item.name
        key = os.path.dirname(filename)
        filename = os.path.basename(filename)

        if key not in result:
            result[key] = {}
        example = result[key]

        name, ext = os.path.splitext(filename)
        example[name] = item

    return result


def phoneme_transcription(label):
    # REQ: This MUST be kept in sync with
    # datapipes.mfa_out.normalize_transcript.
    allowed_punctuation = '.?!,;"'

    # contains phonemes and associated time intervals
    label_phones = label['phones']
    # contains normalized words and associated time intervals
    label_words = label['words']
    # contains the original transcript
    transcript = label['utterance']['content']

    # words and phones are associate with time intervals, which can be
    # use to convert words to phonemes

    # words are also normalized versions of what appears in the
    # transcript, so they can be used to tokenize the transcription

    # step 1: figure out how phonemes group into words
    # we'll assign each phoneme to a group such that each group corresponds
    # to a single word in the transcription

    phone_groups = []  # each group will correspond to a single word
    word_idx = 0  # index of the last unused word
    new_group = True  # True iff the next phoneme belongs to a new word
    for ph in label_phones:
        if ph['content'] in ('sil', 'sp'):
            # MFA uses these to pad an utterance when intervals don't
            # belong to any word in the transcription
            continue

        # if the current phone begins after the current word ends...
        if ph['interval'][0] >= label_words[word_idx]['interval'][-1]:
            # make sure the phone goes into the group associated with
            # the next word
            new_group = True
            # and move onto the next word
            word_idx += 1

        # if the current phone belongs in a new group...
        if new_group:
            # add it to its own group (list), and append that group to
            # phone_groups
            phone_groups.append([ph['content']])
            new_group = False
        else:
            # else add it to the current group
            phone_groups[-1].append(ph['content'])

    # sanity check: each word decomposes uniquely into a phone group
    assert len(phone_groups) == len(label_words)

    # step 2: figure out how the transcript is associated with words
    # we'll assign each character in the transcription to a "word" such that
    # EITHER the word can be converted directly into phonemes OR the "word"
    # is a punctuation symbol and can be copied into the result

    # normalize the transcript so they'll exactly match the MFA-output words
    norm_transcript = transcript.replace('-', '').replace("'", '').lower()
    new_word = True  # True iff the next character belongs to a new word
    transc_words = [
    ]  # contains each word and punctuation as a separate item...
    punctuation_count = 0  # count for a later sanity check

    for c in norm_transcript:
        if c == ' ':
            # make sure the next character is assigned to a new "word"
            new_word = True
        elif c in allowed_punctuation:
            # each punctuation symbol is assigned its own "word"
            transc_words.append(c)
            # remember this for a later sanity check
            punctuation_count += 1
            new_word = True
        else:
            if new_word:
                # put the character into a new list item ("word")
                transc_words.append(c)
                new_word = False
            else:
                # append the character to the current "word"
                transc_words[-1] += c

    # in total, each word and each punctuation mark should be represented
    # in word_seq
    assert len(transc_words) == len(label_words) + punctuation_count

    # step 3: convert each word in word_seq into its phoneme sequence
    # this will be a 1-to-1 conversion of words to phonemes while retaining
    # any punctuation "words"

    # so far, we've tokenized the transcription, but we don't know if the
    # tokenized words actually match the words recognized by MFA...
    # we'll validate the tokens while doing the conversion

    result = ''
    word_idx = 0  # keep track of the next word we'll need to match
    for w in transc_words:
        if w in allowed_punctuation:
            # append punctuation without any conversion
            result += w
        elif w == label_words[word_idx]['content']:
            # the tokenized word w matches the expected MFA word
            # add its phoneme conversion to the result
            conversion = ' '.join(phone_groups[word_idx])
            result += ' {%s}' % conversion
            # start trying to match the next MFA word
            word_idx += 1
        else:
            raise Exception(
                f'transcription ("{norm_transcript}") contains an ' +
                f'unknown word ("{w}") in {label["key"]}')

    # sanity check: every word should have been converted
    assert word_idx == len(label_words)

    return result.strip()
