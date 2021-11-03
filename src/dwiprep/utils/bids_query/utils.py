from typing import List, Union
from pathlib import Path

from bids.layout.layout import BIDSLayout

#: Queries for BIDSLayout
DWI_QUERY: dict = {"datatype": "dwi", "suffix": "dwi"}
FMAP_QUERY: dict = {"datatype": "fmap"}
T1W_QUERY: dict = {"datatype": "anat", "suffix": "T1w"}
T2W_QUERY: dict = {"datatype": "anat", "suffix": "T2w"}

#: Recognized file extensions.
FILE_EXTENSIONS: List[str] = ["nii", "nii.gz"]

#: File types and corresponding suffixes
FILE_TYPES_BY_EXTENSIONS: dict = {
    "bval": ["bval"],
    "bvec": ["bvec"],
    "json": ["json"],
    "nifti": ["nii", "nii.gz"],
}

#: BIDS-compatible entity pattern

ENTITY_PATTERN: str = "{key}-{value}"


def has_fieldmap(session_data: dict) -> bool:
    """
    Whether fieldmap are available for current session

    Parameters
    ----------
    session_data : dict
        Session data (output of `BidsQuery.collect_data)

    Returns
    -------
    bool
        Whether fieldmap are available for current session
    """
    return len(session_data.get("fmap")) > 0


def infer_phase_encoding_direction(
    layout: BIDSLayout, file_name: Union[Path, str]
) -> str:
    """
    Used *layout* to query the phase encoding direction used for *file_name* in <AP,PA,etc.> format.

    Parameters
    ----------
    layout : BIDSLayout
        An instantiated BIDSLayout
    file_name : Union[Path,str]
        DWI series to query

    Returns
    -------
    str
        Phase encoding direction.
    """
    return layout.parse_file_entities(file_name).get("direction")


def query_fieldmap(layout: BIDSLayout, fieldmap: list):
    fieldmap_by_direction = {}
    for f in fieldmap:
        pe = infer_phase_encoding_direction(layout, f)
        fieldmap_by_direction[f"fmap_{pe}"] = f
    return fieldmap_by_direction


def rename_session_data_by_fieldmap(
    layout: BIDSLayout, session_data: dict
) -> dict:
    if has_fieldmap(session_data):
        fieldmap = session_data.pop("fmap")
        fieldmap_by_direction = query_fieldmap(layout, fieldmap)
        for key, val in fieldmap_by_direction.items():
            session_data[key] = val
    return session_data
