import json
import math
import os
import tarfile

import librosa
import numpy as np
import parselmouth

from datapipes.fileutils import *
from ponysynth import pyglottal


class AudioInfoGenerator:
    def __init__(self, outfile_fn: str):
        self.output_fn = VerifiedFile(outfile_fn).path

    def generate_result(self, reference: str, audio_file):
        output_info_path = os.path.join(reference, 'info.json')

        samples, rate = librosa.core.load(audio_file, sr=None)
        info = _get_audio_info(samples, rate)
        info_data = json.dumps(info).encode('utf-8')

        if datapipes.__dry_run__:
            return

        write_tardata(self.output_tar, output_info_path, info_data)

    def __enter__(self):
        self.output_tar = tarfile.open(self.output_fn, 'w:xz')
        return self

    def __exit__(self, type, value, traceback):
        self.output_tar.close()


_round5 = lambda x: str(round(x, -int(math.floor(math.log10(abs(x)))) + 4))


def _get_formants_info(formants):
    result = []
    for t in formants.t_grid():
        bin_info = {'time.sec': _round5(t)}

        for i in range(1, 4):
            center = formants.get_value_at_time(i, t)
            if math.isnan(center):
                break

            bandwidth = formants.get_bandwidth_at_time(i, t)
            bin_info['F{}'.format(i)] = {
                'centre.hz': _round5(center),
                'bandwidth.hz': _round5(bandwidth)
            }

        result.append(bin_info)

    return result


def _get_pitch_info(pitch):
    result = []
    times = pitch.xs()
    pitches = pitch.selected_array['frequency']
    strengths = pitch.selected_array['strength']

    for i in range(len(times)):
        if pitches[i] == 0 or math.isnan(pitches[i]):
            continue

        result.append({
            'time.sec': _round5(times[i]),
            'pitch.hz': _round5(pitches[i]),
            'strength.corr': _round5(strengths[i])
        })

    return result


def _get_intensity_info(intensity):
    result = []
    times = intensity.xs()
    intensities = intensity.values.T.flatten()

    for i in range(len(times)):
        if intensities[i] == 0 or math.isnan(intensities[i]):
            continue

        result.append({
            'time.sec': _round5(times[i]),
            'volume.db': _round5(intensities[i])
        })

    return result


def _get_audio_info(samples, rate):
    sound = parselmouth.Sound(samples, rate)
    formants = sound.to_formant_burg(max_number_of_formants=3)
    pitch = sound.to_pitch()
    intensity = sound.to_intensity()

    gcis = np.array(pyglottal.quick_gci(samples), dtype=np.float32)
    gcis = gcis.flatten() / rate

    return {
        'formants': _get_formants_info(formants),
        'pitch': _get_pitch_info(pitch),
        'intensity': _get_intensity_info(intensity),
        'gci.sec': [str(x) for x in gcis]
    }
