"""
Definition of the data collection and validation functions used by the DWIprep
preprocessing workflow.
"""
from pathlib import Path
from typing import List, Union, Tuple

from bids import BIDSLayout
from bids.layout.models import BIDSFile

#: Queries for BIDSLayout
DWI_QUERY = {"datatype": "dwi", "suffix": "dwi"}
FMAP_QUERY: dict = {"datatype": "fmap"}
T1W_QUERY = {"datatype": "anat", "suffix": "T1w"}
T2W_QUERY = {"datatype": "anat", "suffix": "T2w"}

#: Recognized file extensions.
FILE_EXTENSIONS: List[str] = ["nii", "nii.gz"]

#: File types and corresponding suffixes
FILE_TYPES_BY_EXTENSIONS = {
    "bval": ["bval"],
    "bvec": ["bvec"],
    "json": ["json"],
    "nifti": ["nii", "nii.gz"],
}


ENTITY_PATTERN: str = "{key}-{value}"


class BidsQuery:
    def __init__(self) -> None:
        """
        Initiates a BidsQuery instance.
        """

    def collect_data(
        self,
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
        tuple
            Required preprocessing data

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

    def validate_file(self, rules: dict, file_name: dict):
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

    def get_associated(
        self, layout: BIDSLayout, file_name: str
    ) -> list[BIDSFile]:
        """Get all files assocated to *file_name*.

        Parameters
        ----------
        layout : BIDSLayout
            *pybids* BIDSLayout instance.
        file_name : str
            File to locate

        Returns
        -------
        list[BIDSFile]
            List of all BIDSFile instances that are associated with *file_name*
        """
        bids_file = layout.get_file(file_name)
        assoc_json = [
            j
            for j in bids_file.get_associations()
            if j.entities.get("extension") == ".json"
        ]
        return (
            assoc_json + assoc_json[0].get_associations()
            if assoc_json
            else None
        )

    def parse_associated_files(associated_files: list):
        parsed_files = {}
        for file_name in associated_files:
            extension = file_name.get_entities().get("extension").strip(".")
            file_type = [
                key
                for key, value in FILE_TYPES_BY_EXTENSIONS.items()
                if extension in value
            ]
            if file_type:
                parsed_files[file_type[0]] = file_name.path
        return parsed_files
