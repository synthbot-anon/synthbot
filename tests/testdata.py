from ponysynth.speech_corpus import load_audio, load_utterance


class OnceUponATime:
	sheaf = load_audio('tests/data/once-upon-a-time.wav')
	utterance = load_utterance('tests/data/once-upon-a-time.TextGrid', sheaf)
	expected_content = \
			['W', 'AH1', 'N', 'S', 'AH0', 'P', 'AA1', 'N', 'EY1', 'T', 'AY1', 'M', 'sp']
