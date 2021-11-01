from bids import BIDSLayout
from typing import Union
from pathlib import Path
from nipype.interfaces.io import DataGrabber

MANDATORY_ENTITIES = ["dwi"]

RECOMMENDED_ENTITIES = ["fmap"]

RELEVANT_DATA_TYPES = ["dwi", "fmap"]

WORK_DIR_NAME = "dmriprep_wf"

OUTPUT_ENTITIES = {"raw_mif": {"description": "orig"}}

OUTPUT_PATTERNS = "sub-{subject}/[ses-{session}/][{datatype}/]sub-{subject}[_ses-{session}][_acq-{acquisition}][_dir-{direction}][_space-{space}][_desc-{description}]_{suffix}.{extension}"

STARTING_TEMPLATES = {
    "dwi": "dwi/sub-%s*_dwi.mif",
    "fmap": "fmap/sub-%s*.mif",
}


def get_data_grabber():
    datagrabber = DataGrabber(
        infields=["subject_id"], outfields=["dwi", "fmap"]
    )
    datagrabber.inputs.template = "*"
    datagrabber.inputs.sort_filelist = True
    datagrabber.inputs.field_template = STARTING_TEMPLATES
    return datagrabber


def infer_phase_encoding_direction(
    layout: BIDSLayout, file_name: Union[Path, str]
) -> str:
    """
    Used *layout* to query the phase encoding direction used for *file_name*.

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
    bids_file = layout.get_file(file_name)
    if not bids_file:
        raise FileNotFoundError(
            "A valid DWI series must be provided to infer phase encoding direction!"
        )
    return bids_file.get_metadata().get("PhaseEncodingDirection")


def get_relevant_files(session_data: dict):
    """
    Generates the pipeline's "starting node"

    Parameters
    ----------
    session_data : dict
        A dictionary with the locations of all necessary session's data

    Returns
    -------
    str,str
        The "starting" node for processing
    """
    return session_data.get("dwi"), session_data.get("fmap")
