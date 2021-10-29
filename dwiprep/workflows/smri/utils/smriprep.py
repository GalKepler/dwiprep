import os
from pathlib import Path

PATH_LIKE_KWARGS = [
    "bids-filter-file",
    "fs-license-file",
    "fs-subjects-dir",
    "work-dir",
    "w",
]

ALLOWED_BIDS_ENTITIES = ["t1w", "t2w"]

DEFAULT_KWARGS = {"--output-spaces": ["MNI152NLin2009cAsym", "anat"]}


def validate_queries(queries: dict) -> dict:
    """[summary]

    Parameters
    ----------
    queries : dict
        [description]

    Returns
    -------
    dict
        [description]
    """
    return {
        key: value
        for key, value in queries.items()
        if key in ALLOWED_BIDS_ENTITIES
    }


def locate_fs_license_file():
    fs_home = os.environ.get("FREESURFER_HOME")
    fs_license = Path(fs_home) / "license.txt"
    return fs_license if fs_license.exists() else None
