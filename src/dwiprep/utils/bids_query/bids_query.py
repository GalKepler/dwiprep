"""
Definition of the data collection and validation functions used by the DWIprep
preprocessing workflow.
"""
from pathlib import Path
from typing import List, Union

from bids import BIDSLayout
<<<<<<< HEAD:dwiprep/utils/bids_query/bids_query.py
from typing import Union, Tuple
=======
>>>>>>> master:src/dwiprep/utils/bids_query/bids_query.py

DWI_QUERY = {"datatype": "dwi", "suffix": "dwi"}
FMAP_QUERY: dict = {"datatype": "fmap"}
T1W_QUERY = {"datatype": "anat", "suffix": "T1w"}
T2W_QUERY = {"datatype": "anat", "suffix": "T2w"}

FILE_EXTENSIONS: List[str] = ["nii", "nii.gz"]

ENTITY_PATTERN: str = "{key}-{value}"


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
    Collects processing-relevant files from a BIDS dataset.

    Parameters
    ----------
    bids_dir : Union[BIDSLayout, Path, str]
        Either BIDSLayout or path-like object representing an existing
        BIDS-compatible dataset
    participant_label : str
        String representing a subject existing within *bids_dir*
    bids_validate : bool, optional
        Whether to validate *bids_dir*`s compatibility with the BIDS format,
        by default True

    Returns
    -------
<<<<<<< HEAD:dwiprep/utils/bids_query/bids_query.py
    dict
        Paths to subject's processing-relevant files with corresponding keys.
    BIDSLayout
        *bids_dir*'s corresponding *pybids*'s BIDSLayout instance
    dict
        Both automatic (mandatory) and user-defined definition of processining-relevant BIDS entities.
=======
    tuple
        Required preprocessing data
>>>>>>> master:src/dwiprep/utils/bids_query/bids_query.py
    """
    if isinstance(bids_dir, BIDSLayout):
        layout = bids_dir
    else:
        layout = BIDSLayout(str(bids_dir), bids_validate)
    queries = {
        "dwi": {**DWI_QUERY, **dwi_identifier},
        "fmap": {**FMAP_QUERY, **fmap_identifier},
        "t1w": {**T1W_QUERY, **t1w_identifier},
        "t2w": {**T2W_QUERY, **t2w_identifier},
    }

    subj_data = {
        dtype: sorted(
            layout.get(
                return_type="file",
                subject=participant_label,
                extension=FILE_EXTENSIONS,
                **query,
            )
        )
        for dtype, query in queries.items()
    }

    return subj_data, layout, queries


def validate_file(rules: dict, file_name: dict):
    """
    Validates files by BIDS-compatible identifiers.

    Parameters
    ----------
    rules : dict
        Dictionary with keys of BIDS-recognized key and their accepted
        values
    file_name : str
        File to validate
    """
    valid = []
    for key, value in rules.items():
        pattern = ENTITY_PATTERN.format(key=key, value=value)
        valid.append(pattern in file_name)
    return all(valid)
