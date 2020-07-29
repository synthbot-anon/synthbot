import os
import pandas


class FileCollector:
    def __init__(self):
        self.domain = ["directory_path"]
        self.codomain = ["file_path"]

    def execute(self, frame):
        def _gen():
            for data in frame.itertuples():
                path = data.directory_path
                for dirpath, dirnames, filenames in os.walk(path):
                    for fn in filenames:
                        yield f"{dirpath}/{fn}"

        result = pandas.DataFrame(_gen(), columns=["file_path"])
        return result


class TextFileFilter:
    def __init__(self):
        self.domain = ["file_path"]
        self.codomain = ["text_path"]

    def execute(self, frame):
        def _gen():
            for data in frame.itertuples():
                ext = os.path.splitext(data.file_path)[-1].lower()
                if ext == ".txt":
                    yield data.file_path

        result = pandas.DataFrame(_gen(), columns=["text_path"])
        return result


class AudioFileFilter:
    def __init__(self):
        self.domain = ["file_path"]
        self.codomain = ["audio_path"]

    def execute(self, frame):
        def _gen():
            for data in frame.itertuples():
                ext = os.path.splitext(data.file_path)[-1].lower()
                if ext in (".wav", ".flac", ".mp3"):
                    yield data.file_path

        result = pandas.DataFrame(_gen(), columns=["audio_path"])
        return result


class CsvFileParser:
    def __init__(self, codomain, header="infer", sep=","):
        self.domain = ["csv_path"]
        self.codomain = codomain
        self.header = header
        self.sep = sep

    def execute(self, frame):
        def _gen():
            for data in frame.itertuples():
                try:
                    contents = pandas.read_csv(
                        data.text_path,
                        header=self.header,
                        sep=self.sep,
                        names=self.codomain,
                        error_bad_lines=True,
                    )

                    if contents.isnull().any().any():
                        continue

                    yield contents

                except pandas.errors.ParserError:
                    pass

        return pandas.concat(_gen(), ignore_index=True)


class FilenameMatcher:
    def execute(self, left, right):
        def _gen_target_join():
            for index, path in left.iteritems():
                filename = os.path.basename(path)
                yield {"target_index": index, "filename": filename}

        def _gen_reference_join():
            for index, path in right.iteritems():
                filename = os.path.basename(path)
                yield {"reference_index": index, "filename": filename}

        target_join = pandas.DataFrame(_gen_target_join())
        reference_join = pandas.DataFrame(_gen_reference_join())

        joined_frame = pandas.merge(
            target_join, reference_join, how="inner", on="filename"
        )
        joined_frame.drop(columns=["filename"], inplace=True)

        return joined_frame


class TacotronDatasetLoader:
    def __init__(self):
        self.directories = set()

    def load_directory(self, path):
        self.directories.add(path)

    def pandas(self):
        directories = pandas.DataFrame(self.directories, columns=["directory_path"])
        files = FileCollector().execute(directories)

        text_files = TextFileFilter().execute(files)
        filelists = CsvFileParser(
            header=None, sep="|", codomain=["audio_reference", "transcript"]
        ).execute(text_files)

        audio_files = AudioFileFilter().execute(files)

        matcher = FilenameMatcher()
        joiner = matcher.execute(
            filelists["audio_reference"], audio_files["audio_path"]
        )

        merged = pandas.merge(
            filelists, joiner, how="outer", left_index=True, right_on="reference_index"
        )
        merged = pandas.merge(
            merged, audio_files, how="outer", left_on="target_index", right_index=True
        )
        merged.reset_index(inplace=True)
        merged.drop(columns=["reference_index", "target_index", "index"], inplace=True)

        return merged


class TacotronDatasetWriter:
    def __init__(self):
        self.data = []

    def load_data(self, pandas):
        self.data.append(pandas)
