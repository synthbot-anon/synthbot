import dataclasses
import os
from typing import Dict, Set

import datapipes.common
import datapipes.clipper
from datapipes.datasets import clipper_mlp_values
from datapipes.datasets import clipper_other_values

from datapipes.datasets.clipper_datasets import ClipperParamsHelper


class DariaParams(ClipperParamsHelper):
    def __init__(self, clipper_root):
        super(DariaParams, self).__init__(
            clipper_root,
            characters={"Daria": "Daria"},
            tags={"Neutral": "Neutral"},
            noise_levels={"": ""},
            sources={
                "M1/": "daria:m1",
                "M2/": "daria:m2",
                "S1/E1/": "daria:s1e1",
                "S1/E12/": "daria:s1e12",
                "S1/E2/": "daria:s1e2",
                "S1/E7/": "daria:s1e7",
                "S1/E3/": "daria:s1e3",
                "S1/E9/": "daria:s1e9",
                "S1/E5/": "daria:s1e5",
                "S1/E10/": "daria:s1e10",
                "S1/E4/": "daria:s1e4",
                "S1/E6/": "daria:s1e6",
                "S1/E11/": "daria:s1e11",
                "S1/E8/": "daria:s1e8",
                "S1/E13/": "daria:s1e13",
                "S2/E1/": "daria:s2e1",
                "S2/E12/": "daria:s2e12",
                "S2/E2/": "daria:s2e2",
                "S2/E7/": "daria:s2e7",
                "S2/E3/": "daria:s2e3",
                "S2/E9/": "daria:s2e9",
                "S2/E5/": "daria:s2e5",
                "S2/E10/": "daria:s2e10",
                "S2/E4/": "daria:s2e4",
                "S2/E6/": "daria:s2e6",
                "S2/E11/": "daria:s2e11",
                "S2/E8/": "daria:s2e8",
                "S2/E13/": "daria:s2e13",
                "S5/E1/": "daria:s5e1",
                "S5/E12/": "daria:s5e12",
                "S5/E2/": "daria:s5e2",
                "S5/E7/": "daria:s5e7",
                "S5/E3/": "daria:s5e3",
                "S5/E9/": "daria:s5e9",
                "S5/E5/": "daria:s5e5",
                "S5/E10/": "daria:s5e10",
                "S5/E4/": "daria:s5e4",
                "S5/E6/": "daria:s5e6",
                "S5/E11/": "daria:s5e11",
                "S5/E8/": "daria:s5e8",
                "S5/E13/": "daria:s5e13",
                "S4/E1/": "daria:s4e1",
                "S4/E12/": "daria:s4e12",
                "S4/E2/": "daria:s4e2",
                "S4/E7/": "daria:s4e7",
                "S4/E3/": "daria:s4e3",
                "S4/E9/": "daria:s4e9",
                "S4/E5/": "daria:s4e5",
                "S4/E10/": "daria:s4e10",
                "S4/E4/": "daria:s4e4",
                "S4/E6/": "daria:s4e6",
                "S4/E11/": "daria:s4e11",
                "S4/E8/": "daria:s4e8",
                "S4/E13/": "daria:s4e13",
                "S3/E1/": "daria:s3e1",
                "S3/E12/": "daria:s3e12",
                "S3/E2/": "daria:s3e2",
                "S3/E7/": "daria:s3e7",
                "S3/E3/": "daria:s3e3",
                "S3/E9/": "daria:s3e9",
                "S3/E5/": "daria:s3e5",
                "S3/E10/": "daria:s3e10",
                "S3/E4/": "daria:s3e4",
                "S3/E6/": "daria:s3e6",
                "S3/E11/": "daria:s3e11",
                "S3/E8/": "daria:s3e8",
                "S3/E13/": "daria:s3e13",
            },
        )


def daria_dataset(daria_root):
    daria_params = DariaParams(daria_root)
    daria_dataset = datapipes.clipper.ClipperSet(daria_params)

    for root, dirs, files in os.walk(daria_root):
        for filename in files:
            if filename.endswith(".txt"):
                daria_dataset.load_transcript(f"{root}/{filename}")
            elif filename.endswith(".flac"):
                daria_dataset.load_audio(f"{root}/{filename}")

    return daria_dataset
