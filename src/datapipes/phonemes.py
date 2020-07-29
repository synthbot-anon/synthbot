import pandas
import datapipes.common
import re
import shutil
import os

ALLOWED_PHONEMES = set(
    [
        "AA0",
        "AA1",
        "AA2",
        "AE0",
        "AE1",
        "AE2",
        "AH0",
        "AH1",
        "AH2",
        "AO0",
        "AO1",
        "AO2",
        "AW0",
        "AW1",
        "AW2",
        "AY0",
        "AY1",
        "AY2",
        "B",
        "CH",
        "D",
        "DH",
        "EH0",
        "EH1",
        "EH2",
        "ER0",
        "ER1",
        "ER2",
        "EY0",
        "EY1",
        "EY2",
        "F",
        "G",
        "HH",
        "IH0",
        "IH1",
        "IH2",
        "IY0",
        "IY1",
        "IY2",
        "JH",
        "K",
        "L",
        "M",
        "N",
        "NG",
        "OW0",
        "OW1",
        "OW2",
        "OY0",
        "OY1",
        "OY2",
        "P",
        "R",
        "S",
        "SH",
        "T",
        "TH",
        "UH0",
        "UH1",
        "UH2",
        "UW0",
        "UW1",
        "UW2",
        "V",
        "W",
        "Y",
        "Z",
        "ZH",
    ]
)


class PhoneticDictionary:
    def __init__(self):
        self.dictionary = {}

    def load_dictionary(self, dictionary_path, verbose=True):
        logger = datapipes.common.logger(verbose)

        with open(dictionary_path, encoding="utf-8") as infile:
            for line in logger.tqdm(
                infile.read().split("\n"), desc=f"Scanning {dictionary_path}"
            ):
                # remove comments
                if "//" in line:
                    comment_start = line.find("//")
                    line = line[:comment_start]

                # normalize the pronunciations
                line = line.replace("-", "").replace("'", "")
                line = line.strip().upper()

                # ignore blank lines
                if line == "":
                    continue

                # line format: word phm1 phm2 phm3 ...
                separated = line.split()
                word = separated[0]
                phonemes = list(filter(lambda x: x, separated[1:]))

                if not phonemes:
                    print(f"Missing pronunciation for {word} in {dictionary_path}")
                    continue

                for ph in phonemes:
                    if ph not in ALLOWED_PHONEMES:
                        print(
                            f"Invalid phoneme {ph} "
                            f"in {line} of {dictionary_path}. Allowed phonemes "
                            f"are: {ALLOWED_PHONEMES}"
                        )
                        break
                else:
                    self.dictionary[word] = self.dictionary.get(word, set())
                    self.dictionary[word].add(" ".join(phonemes))

    def pandas(self, verbose=True):
        result = []
        logger = datapipes.common.logger(verbose)

        for word, phonemes in logger.tqdm(
            self.dictionary.items(), desc="Creating dataframe"
        ):
            for pronunciation in phonemes:
                result.append([word, pronunciation])

        return pandas.DataFrame(result, columns=["word", "pronunciation"])

    def dict(self):
        result = {}
        for row in self.pandas().itertuples():
            result[row.word] = row.pronunciation

        return result

    def debugger(self, output_path):
        return HorseWordsDebugger(self.dictionary, output_path)


class HorseWordsDebugger:
    def __init__(self, dictionary, output_path):
        self.dictionary = dictionary
        self.output_path = output_path

        if not os.path.exists(output_path):
            os.makedirs(output_path)
        else:
            if not os.path.isdir(output_path):
                print(f"Warning: some file already exists at path {output_path}")
                self.output_path = None

    def check_transcripts(self, audio, verbose=True):
        missing_data = []

        for data in audio.itertuples():
            transcript_words = re.split(r"[ ]", data.transcript)
            transcript_words = [x for x in transcript_words if x]

            for word in transcript_words:
                word_lookup = re.sub(r"[.!?,\-\';#]", "", word).upper()
                if not word_lookup:
                    continue

                if word_lookup not in self.dictionary:
                    new_filename = f"{word.upper()} - {data.transcript}"
                    self.copy_file(data.audio_path, new_filename)

                    missing_data.append(
                        [word, data.source, data.start, data.transcript]
                    )

        result = pandas.DataFrame(
            missing_data, columns=["missing_word", "source", "start", "transcript"]
        )
        result.sort_values(["source", "start"])
        return result

    def copy_file(self, old_path, new_name):
        extension = os.path.splitext(old_path)[1]
        shutil.copyfile(old_path, f"{self.output_path}/{new_name}{extension}")


def create_arpa_converter(dictionary):
    def arpa(text):
        out = ""
        for word_ in text.split(" "):
            word = word_
            end_chars = ""
            while any(elem in word for elem in r"!?,.;") and len(word) > 1:
                if word[-1] == "!":
                    end_chars = "!" + end_chars
                    word = word[:-1]
                if word[-1] == "?":
                    end_chars = "?" + end_chars
                    word = word[:-1]
                if word[-1] == ",":
                    end_chars = "," + end_chars
                    word = word[:-1]
                if word[-1] == ".":
                    end_chars = "." + end_chars
                    word = word[:-1]
                if word[-1] == ";":
                    end_chars = ";" + end_chars
                    word = word[:-1]
                else:
                    break
            try:
                word_arpa = dictionary[word.upper()]
            except:
                word_arpa = ""
            if len(word_arpa) != 0:
                word = "{" + str(word_arpa) + "}"
            out = (out + " " + word + end_chars).strip()
        return out

    return arpa


class CookiePhonemeTranscriber:
    def __init__(self):
        self.dictionary = {}
        self.transcripts = []

    def load_phoneme_dict(self, pandas):
        for row in pandas.itertuples():
            self.dictionary[row.word] = row.pronunciation

    def load_transcripts(self, pandas):
        self.transcripts.append(pandas)

    def pandas(self, verbose=True, all_files=False):
        arpa_converter = create_arpa_converter(self.dictionary)
        result = []

        transcripts = pandas.concat(self.transcripts)

        def _gen():
            for row in transcripts.itertuples():
                yield row.Index, arpa_converter(row.transcript)

        frame = pandas.DataFrame(_gen(), columns=["index", "phonemes"])
        frame.set_index("index", inplace=True, drop=True)
        return frame

    def augment(self):
        transcripts = pandas.concat(self.transcripts)
        phonemes = self.pandas()

        return pandas.merge(
            transcripts, phonemes, how="right", left_index=True, right_index=True
        )

    def debugger(self):
        pass


class PhonemeDebugger:
    def __init__(self):
        pass

    def run_tests(self):
        pass
