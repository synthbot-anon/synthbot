from datapipes.datasets import clipper_mlp_values
import datapipes.clipper
import os
import datapipes.common


def mlp_dialogue_params():
    def characters(candidate):
        return clipper_mlp_values.CHARACTERS[candidate]

    def tags(candidate):
        return clipper_mlp_values.TAGS[candidate]

    def noise_levels(candidate):
        return clipper_mlp_values.NOISE[candidate]

    def sources(candidate):
        key = datapipes.common.parse_name(candidate)
        if key == 'labels':
            print('found labels.txt:', candidate)
            key = datapipes.common.parse_parent_name(candidate)
            print('replacing with', key)

        return clipper_mlp_values.EPISODES[key]

    return datapipes.clipper.ClipperParams(characters, tags, noise_levels,
                                           sources)


def mlp_dialogue_dataset(clipper_root):
    params = mlp_dialogue_params()
    dataset = datapipes.clipper.ClipperSet(params)

    for entry in os.scandir(f'{clipper_root}/Reviewed episodes'):
        if not entry.is_file():
            print(f'Unexpected directory: Reviewed episodes/{entry.name}')
            continue
        dataset.load_ponysorter(entry.path)

    clip_directories = [
        f'{clipper_root}/Sliced Dialogue/EQG',
        f'{clipper_root}/Sliced Dialogue/FiM',
        f'{clipper_root}/Sliced Dialogue/MLP Movie',
        f'{clipper_root}/Sliced Dialogue/Special source',
        f'{clipper_root}/Other/Mobile game',
    ]

    for clip_directory in clip_directories:
        print('loading', clip_directory)
        for root, dirs, files in os.walk(clip_directory):
            for filename in files:
                if filename == 'labels.txt':
                    continue

                if filename.endswith('.txt'):
                    dataset.load_transcript(f'{root}/{filename}')
                elif filename.endswith('.flac'):
                    dataset.load_audio(f'{root}/{filename}')
                else:
                    print(f'Unexpected file: {root}/{filename}')

    for entry in os.scandir(f'{clipper_root}/Sliced Dialogue/Label files'):
        if not entry.is_file():
            continue
        if entry.name == 'songs.txt':
            continue
        dataset.load_audacity(entry.path)

    dataset.load_audacity(f'{clipper_root}/Sliced Dialogue/MLP Movie/labels.txt')

    return dataset
