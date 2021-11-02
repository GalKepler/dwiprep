from bids import BIDSLayout
from typing import Union
from pathlib import Path
from nipype.interfaces.io import DataGrabber
from niworkflows.interfaces.bids import DerivativesDataSink

MANDATORY_ENTITIES = ["dwi"]

RECOMMENDED_ENTITIES = ["fmap"]

RELEVANT_DATA_TYPES = ["dwi", "fmap"]

WORK_DIR_NAME = "dmriprep_wf"

OUTPUT_ENTITIES = {"raw_mif": {"description": "orig", "extension": "mif"}}

OUTPUT_PATTERNS = "sub-{subject}/[ses-{session}/][{datatype}/]sub-{subject}[_ses-{session}][_acq-{acquisition}][_dir-{direction}][_space-{space}][_desc-{description}]_{suffix}.{extension}"

STARTING_TEMPLATES = {
    "dwi": "dwi/sub-%s*desc-orig*dwi.mif",
    "fmap": "fmap/sub-%s*desc-orig*.mif",
}


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


def infer_phase_encoding_direction_mif(in_file: str) -> str:
    """
    Utilizes *mrinfo* for a specific query of phase encoding direction.

    Parameters
    ----------
    in_file : str
        File to query

    Returns
    -------
    str
        Phase Encoding Direction as denoted in *in_file*`s header.
    """
    import subprocess

    return (
        subprocess.check_output(
            ["mrinfo", str(in_file), "-property", "PhaseEncodingDirection"]
        )
        .decode("utf-8")
        .replace("\n", "")
    )


def check_opposite_phase_encoding(layout: BIDSLayout, fmap: list, dwi: list):
    """
    Checks whether to extract mean B0 image from DWI series and use it for SDC.

    Parameters
    ----------
    layout : BIDSLayout
        BIDSLayout instance describing a valid dataset
    fmap : list
        List of files that are associated with the fieldmap.
    dwi : list
        List of files that are associated with the DWI series.

    Returns
    -------
    bool
        Whether to extract B0 image and run SDC.
    """
    extract_b0 = True
    run_sdc = True
    fmap = [f for f in fmap if ".nii" in Path(f).name]
    dwi = [f for f in dwi if ".nii" in Path(f).name]
    fmap_directions = [infer_phase_encoding_direction(layout, f) for f in fmap]

    if len(set(fmap_directions)) > 1:
        extract_b0 = False

    dwi_directions = [infer_phase_encoding_direction(layout, f) for f in dwi]
    if len(set(dwi_directions + fmap_directions)) < 2:
        extract_b0 = False
        run_sdc = False
    return extract_b0, run_sdc


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
