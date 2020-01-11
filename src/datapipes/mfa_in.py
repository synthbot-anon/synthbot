from datapipes.fileutils import *
from praatio import tgio

INPUT_ALIGNMENT_FORMAT = '.textgrid'


class MFADataset(LocalFiles):
    def __init__(self, folder: str):
        LocalFiles.__init__(self, folder)

    def _accept_path(self, path: str):
        return os.path.splitext(path)[-1].lower() == INPUT_ALIGNMENT_FORMAT

    def _wrap_path(self, path: str):
        return MFAAlignmentsFile(path)


def character_from_path(alignment_path: str):
    folder = get_directory(alignment_path)
    return os.path.basename(folder)


class MFAAlignmentsFile:
    def __init__(self, alignment_path: str):
        self.character = character_from_path(alignment_path)
        self.reference = os.path.splitext(get_name(alignment_path))[0]

        alignment_data = tgio.openTextgrid(alignment_path)

        self.words = []
        for word_entry in alignment_data.tierDict['utt - words'].entryList:
            self.words.append({
                'content': word_entry.label,
                'interval': [word_entry.start, word_entry.end]
            })

        self.phones = []
        for phone_entry in alignment_data.tierDict['utt - phones'].entryList:
            self.phones.append({
                'content': phone_entry.label,
                'interval': [phone_entry.start, phone_entry.end]
            })
