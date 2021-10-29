import os
from pathlib import Path
from bids import BIDSLayout
from typing import Union, Tuple

DEFAULT_WORK_DIR_NAME = "work"


def collect_data(
    bids_dir: Union[BIDSLayout, Path, str],
    participant_label: str,
    dwi_identifier: dict,
    fmap_identifier: dict,
    t1w_identifier: dict,
    t2w_identifier: dict,
    bids_validate: bool = True,
) -> Tuple[dict, BIDSLayout, dict]:
    """
    Collects processing-relevant files from a BIDS dataset

    Parameters
    ----------
    bids_dir : Union[BIDSLayout, Path, str]
        Either BIDSLayout or path-like object representing an existing BIDS-compatible dataset.
    participant_label : str
        String representing a subject existing within *bids_dir*.
    bids_validate : bool, optional
        Whether to validate *bids_dir*`s compatibility with the BIDS format, by default True

    Returns
    -------
    dict
        Paths to subject's processing-relevant files with corresponding keys.
    BIDSLayout
        *bids_dir*'s corresponding *pybids*'s BIDSLayout instance
    dict
        Both automatic (mandatory) and user-defined definition of processining-relevant BIDS entities.
    """
    if isinstance(bids_dir, BIDSLayout):
        layout = bids_dir
    else:
        layout = BIDSLayout(str(bids_dir), bids_validate)
    queries = {
        "fmap": {"datatype": "fmap", **fmap_identifier},
        "dwi": {"datatype": "dwi", "suffix": "dwi", **dwi_identifier},
        "t2w": {"datatype": "anat", "suffix": "T2w", **t2w_identifier},
        "t1w": {"datatype": "anat", "suffix": "T1w", **t1w_identifier},
    }

    subj_data = {
        dtype: sorted(
            layout.get(
                return_type="file",
                subject=participant_label,
                extension=["nii", "nii.gz"],
                **query,
            )
        )
        for dtype, query in queries.items()
    }

    return subj_data, layout, queries


def validate_file(rules: dict, fname: dict):
    """
    Validates files by BIDS-compatible identifiers
    Parameters
    ----------
    rules : dict
        Dictionary with keys of BIDS-recognized key and their accepted values.
    fname : str
        File to validate.
    """
    valid = []
    for key, value in rules.items():
        if f"{key}-{value}" in fname:
            valid.append(True)
        else:
            valid.append(False)
    return all(valid)
