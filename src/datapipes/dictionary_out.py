import re
import datapipes
from datapipes.fileutils import VerifiedFile

ALLOWED_PHONEMES = set([
    'AA0', 'AA1', 'AA2', 'AE0', 'AE1', 'AE2', 'AH0', 'AH1', 'AH2', 'AO0',
    'AO1', 'AO2', 'AW0', 'AW1', 'AW2', 'AY0', 'AY1', 'AY2', 'B', 'CH', 'D',
    'DH', 'EH0', 'EH1', 'EH2', 'ER0', 'ER1', 'ER2', 'EY0', 'EY1', 'EY2', 'F',
    'G', 'HH', 'IH0', 'IH1', 'IH2', 'IY0', 'IY1', 'IY2', 'JH', 'K', 'L', 'M',
    'N', 'NG', 'OW0', 'OW1', 'OW2', 'OY0', 'OY1', 'OY2', 'P', 'R', 'S', 'SH',
    'T', 'TH', 'UH0', 'UH1', 'UH2', 'UW0', 'UW1', 'UW2', 'V', 'W', 'Y', 'Z',
    'ZH'
])


class DictionaryGenerator:
    def __init__(self, output_path):
        self.output_path = output_path
        self.dictionary = {}

    def update(self, dictionary_path):
        with open(dictionary_path, encoding='utf-8') as infile:
            for line in infile.read().split('\n'):
                # remove comments
                if '//' in line:
                    comment_start = line.find('//')
                    line = line[:comment_start]
                line = line.strip().upper()

                # ignore blank lines
                if line == '':
                    continue

                # line format: word phm1 phm2 phm3 ...
                word = line.split(' ')[0].upper()
                pronunciation = line

                phonemes = pronunciation.split()[1:]
                for ph in phonemes:
                    assert ph in ALLOWED_PHONEMES, (
                        f'Invalid pronunciation '
                        f'{pronunciation} in {dictionary_path}. Allowed phonemes '
                        f'are: {ALLOWED_PHONEMES}')

                if pronunciation == word:
                    print('Missing pronunciation for {} in {}'.format(
                        word, dictionary_path))
                    continue

                self.dictionary[word] = self.dictionary.get(word, set())
                self.dictionary[word].add(pronunciation)

    def check_transcripts(self, clipper_files):
        failed = False
        norm_dict = normalized_dict(self.dictionary)

        for clip in clipper_files:
            audio_fn = clip.audio_path
            label = clip.label

            transcript = label['transcript'].upper()
            transcript_words = re.split(r'[ ]', transcript)
            transcript_words = [x for x in transcript_words if x]

            for word in transcript_words:
                dictionary_word = re.sub(r'[.!?,\-\';]', '', word)
                if dictionary_word == '':
                    continue

                if dictionary_word not in norm_dict:
                    normalized_word = re.sub(r'[.!?,\';]', '', word)
                    print(f'Missing pronunciation for {normalized_word}'
                          f'\n\tin {audio_fn}\n\tof {label["source"]}')
                    self.write_file(audio_fn,
                                    f'{normalized_word} - {transcript}.wav')
                    failed = True

        assert not failed, 'Found missing pronunciations'

    def write_file(self, source, destination):
        path = VerifiedFile(
            f'{self.output_path}/missing-words/{destination}').path
        data = open(source, 'rb').read()
        open(path, 'wb').write(data)

    def generate_result(self):
        norm_dict = normalized_dict(self.dictionary)

        if datapipes.__dry_run__:
            return

        write_dict(self.dictionary, f'{self.output_path}/merged.dict.txt')
        write_dict(norm_dict, f'{self.output_path}/normalized.dict.txt')


def write_dict(dictionary, outpath):
    with open(outpath, 'w') as outfile:
        for key in sorted(dictionary.keys()):
            for pronunciation_opt in dictionary[key]:
                outfile.write('{}\n'.format(pronunciation_opt))


def normalized_dict(dictionary):
    result = {}
    for key, value in dictionary.items():
        normalized_key = key.replace('-', '').replace("'", '')
        normalized_value = set()

        for v in value:
            normalized_value.add(v.replace('-', '').replace("'", ''))
        result[normalized_key] = normalized_value

    return result
