from typing import List

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
