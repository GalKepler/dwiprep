from typing import List, Union
from pathlib import Path

from bids.layout.layout import BIDSLayout
from bids.layout.models import BIDSFile

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
#: THEBASE-comaptible identifiers
THE_BASE_IDENTIFIERS = (
    dict(
        dwi_identifier={"direction": "ap"},
        fmap_identifier={"acquisition": "dwi"},
        t1w_identifier={"ceagent": "corrected"},
        t2w_identifier={"ceagent": "corrected"},
    ),
)


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


def get_fieldmaps(dwi_file: str, layout: BIDSLayout):
    """
    Locates all fieldmap associated with *dwi_file* according to the *IntendedFor* field in their corresponding jsons.

    Parameters
    ----------
    dwi_file : str
        dwi NIfTI file
    layout : BIDSLayout
        BIDSLayout instance for the queried bids directory.
    """
    fieldmaps = {}
    dwi_entities = layout.parse_file_entities(dwi_file)
    subject, session = [
        dwi_entities.get(key) for key in ["subject", "session"]
    ]
    available_fieldmaps = layout.get(
        subject=subject,
        session=session,
        datatype="fmap",
        extension=["nii", "nii.gz"],
    )
    target = Path(dwi_file).name
    for fmap in available_fieldmaps:
        intended_for = fmap.get_metadata().get("IntendedFor")
        if isinstance(intended_for, str):
            intended_for = [intended_for]
        intended_for = [Path(f).name for f in intended_for]
        if target in intended_for:
            fmap_dict = add_fieldmap(fmap, layout)
            for key, value in fmap_dict.items():
                fieldmaps[key] = value
    return fieldmaps


def add_fieldmap(fieldmap: BIDSFile, layout: BIDSLayout) -> dict:
    """
    Locates fieldmap-related json file and adds them in an appropriate dictionary with keys that describe their directionality

    Parameters
    ----------
    fieldmap : BIDSFile
        Fieldmap's NIfTI
    layout : BIDSLayout
        BIDSLayout instance for the queried bids directory.

    Returns
    -------
    dict
        Dictionary of fieldmap's NIfTI and json with appropriate keys.
    """
    entities = fieldmap.get_entities()
    entities.pop("fmap")
    direction = entities.get("direction")
    entities["extension"] = "json"
    json = layout.get(**entities)
    fieldmap_dict = {f"fmap_{direction}": fieldmap.path}
    if json:
        fieldmap_dict[f"fmap_{direction}_json"] = json[0].path
    return fieldmap_dict
