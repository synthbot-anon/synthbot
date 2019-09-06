import os
import itertools
from typing import *

import librosa # type: ignore
import soundfile # type: ignore
from praatio import tgio # type: ignore

from ponysynth.indexes import SubstringIndex
from ponysynth.soundsheaf import *


def load_audio(path: str) -> SoundSheaf:
	# TODO: get SoundSheaf to work with any sampling rate
	frames, sample_rate = librosa.load(path, sr=16000)
	length = len(frames) / sample_rate
	box = interval(0, length)
	return SoundSheaf(frames, box)

def load_utterance(transcriptfn: str, sheaf: SoundSheaf) -> Utterance:
	transcript_data = tgio.openTextgrid(transcriptfn)
	phones = []
	for phone_entry in transcript_data.tierDict['utt - phones'].entryList:
		phone_interval = interval(phone_entry.start, phone_entry.end)
		phoneme = phone_entry.label

		phone_sheaf = sheaf.subsheaf(phone_interval)
		phones.append(Phone(phoneme, phone_sheaf))

	return infer_utterance(phones)

def load_character_corpus(audio_folder: str, transcripts_folder: str) -> 'SpeechCorpus':
	result = SpeechCorpus()

	for root, dirs, files in os.walk(transcripts_folder):
		for transcript_fn in files:
			fileroot, ext = os.path.splitext(transcript_fn)

			if ext.lower() != '.textgrid':
				continue
			
			transcript_path = os.path.join(root, transcript_fn)
			basename = os.path.basename(transcript_fn)
			wave_path = os.path.join(audio_folder, '{}.wav'.format(fileroot))

			wavefile = load_audio(wave_path)
			transcript = load_utterance(transcript_path, wavefile)

			result.insert(transcript)

	return result

def infer_diphone(pre: Phone, post: Phone):
	subinterval = interval(pre.sheaf.interval.mid, post.sheaf.interval.mid)
	diphone_sheaf = merge_sheaves(pre.sheaf, post.sheaf).subsheaf(subinterval)
	return Diphone(pre, post, diphone_sheaf)

def infer_utterance(phones: Sequence[Phone]) -> Utterance:
	diphones = [infer_diphone(x[0], x[1]) for x in zip(phones[:-1], phones[1:])]
	diphone_sequence = reduce(merge_diphseq, diphones, DiphoneSequence())
	return merge_utterances(phones[0], diphone_sequence, phones[-1])

class SpeechCorpus:
	# A speech corpus is an collection of utterances.
	
	def __init__(self):
		self.utterances = SubstringIndex()

	def insert(self, utterance: Utterance):
		self.utterances.index(utterance.get_content(), utterance.phones)

	def find_utterances(self, content: Sequence[Content]) -> Generator[Utterance, None, None]:
		options = self.utterances.find(content)
		size = len(content)
		
		for position in options:
			phones, start = position
			end = start + size
			yield infer_utterance(phones[start:end])

	def find_minimal_utterances(self, content_seqs: Sequence[Sequence[Content]]) \
			-> Generator[Sequence[Utterance], None, None]:
		generators = [self.find_utterances(x) for x in content_seqs]
		for result in itertools.product(*generators):
			yield result

	def find_maximal_utterances(self, content: Sequence[Content]) \
			-> Generator[Sequence[Utterance], None, None]:	
		content_seqs = self.find_maximal_content_seqs(tuple(content))
		return self.find_minimal_utterances(content_seqs)

	def find_maximal_content_seqs(self, content: Tuple[Content, ...], _cache = {}):
		if content in _cache:
			return _cache[content]

		if len(content) <= 1:
			result = (content,)
			_cache[content] = result
			return result

		midpoint = int(len(content) / 2)
		left = self.find_maximal_content_seqs(content[:midpoint])
		right = self.find_maximal_content_seqs(content[midpoint:])

		potential_merge = left[-1] + right[0]
		merge_options = self.find_utterances(potential_merge)

		if next(merge_options, None):
			result = left[:-1] + (potential_merge,) + right[1:]
		else:
			result = left + right

		_cache[content] = result
		return result
