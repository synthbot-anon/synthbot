from ponysynth.speech_corpus import *
from tests.testdata import *


def test_normal_load_sequences():
	sheaf = OnceUponATime.sheaf
	utterance = OnceUponATime.utterance
	expected_content = OnceUponATime.expected_content

	loaded_content = utterance.get_content()
	assert loaded_content == expected_content, \
		'Failed to create the correct PhoneSequence'
	
	expected_diphones = list(zip(expected_content[:-1], expected_content[1:]))
	loaded_diphones = [(x.pre.content, x.post.content) for x in utterance.diphones]
	assert loaded_diphones == expected_diphones, \
		'Failed to create the correct diphones'
