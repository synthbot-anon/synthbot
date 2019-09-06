from ponysynth.speechcorpus import *
from tests.testdata import *


def test_find_utterance():
	corpus = SpeechCorpus()
	corpus.insert(OnceUponATime.utterance)

	triphone_utterance = list(corpus.find_utterances(['N', 'S', 'AH0']))
	assert len(triphone_utterance) == 1
	assert triphone_utterance[0].get_start_time() == 0.211 \
		and triphone_utterance[0].get_end_time()  == 0.421, \
		"SpeechCorpus failed to find utterances in 'Once Upon"

	monophone_utterance = list(corpus.find_utterances(['N']))
	monophone_utterance = sorted(monophone_utterance, key=lambda x: x.get_start_time())
	assert len(monophone_utterance) == 2
	assert monophone_utterance[0].get_start_time() == 0.211 \
		and monophone_utterance[0].get_end_time()  == 0.291, \
		"SpeechCorpus failed to find utterance in 'Once'"
	assert monophone_utterance[1].get_start_time() == 0.601 \
		and monophone_utterance[1].get_end_time() == 0.641, \
		"SpeechCorpus failed to find utterance in Upon"

	triphone_sheaf = triphone_utterance[0].get_sheaf()
	assert triphone_sheaf.interval.left > 0, \
		"PhoneSequence sheaf is unnecessarily creating new buffers"

def test_find_minimal_utterances():
	corpus = SpeechCorpus()
	corpus.insert(OnceUponATime.utterance)

	triphone_utterances = list(corpus.find_minimal_utterances([['N'], ['S'], ['AH0']]))
	assert len(triphone_utterances) == 2, \
		'Unable to find the second "N" phone in utterance'
	

def test_find_maximal_utterance():
	corpus = SpeechCorpus()
	corpus.insert(OnceUponATime.utterance)

	triphone_utterance = list(corpus.find_maximal_utterances(('AH0', 'S', 'AH0')))
	assert len(triphone_utterance) == 1, \
		'Unable to find maximal utterance candidate'

