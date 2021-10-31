from bids import BIDSLayout
from typing import Union
from pathlib import Path

MANDATORY_ENTITIES = ["dwi"]

RECOMMENDED_ENTITIES = ["fmap"]

RELEVANT_DATA_TYPES = ["dwi", "fmap"]

WORK_DIR_NAME = "dmriprep_wf"

OUTPUT_ENTITIES = {"raw_mif": {"desc": "orig"}}

OUTPUT_PATTERNS = "sub-{subject}/[ses-{session}/][{datatype}/]sub-{subject}[_ses-{session}][_acq-{acquisition}][_dir-{direction}][_space-{space}][_desc-{desc}]_{suffix}.nii.gz"


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
