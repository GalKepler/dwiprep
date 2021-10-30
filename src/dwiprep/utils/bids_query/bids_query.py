"""
Definition of the data collection and validation functions used by the DWIprep
preprocessing workflow.
"""
from pathlib import Path
from typing import Union, Tuple

from bids import BIDSLayout
from bids.layout.models import BIDSFile

from dwiprep.utils.bids_query.utils import (
    DWI_QUERY,
    FMAP_QUERY,
    T1W_QUERY,
    T2W_QUERY,
    FILE_TYPES_BY_EXTENSIONS,
    FILE_EXTENSIONS,
    ENTITY_PATTERN,
)


class BidsQuery:
    #: Queries for BIDSLayout
    DWI_QUERY = DWI_QUERY
    FMAP_QUERY = FMAP_QUERY
    T1W_QUERY = T1W_QUERY
    T2W_QUERY = T2W_QUERY

    #: Recognized file extensions.
    FILE_EXTENSIONS = FILE_EXTENSIONS

    #: File types and corresponding suffixes
    FILE_TYPES_BY_EXTENSIONS = FILE_TYPES_BY_EXTENSIONS

    #: BIDS-compatible entity pattern
    ENTITY_PATTERN = ENTITY_PATTERN

    def __init__(
        self,
        bids_dir: Union[BIDSLayout, Path, str],
        participant_label: str,
        dwi_identifier: dict,
        fmap_identifier: dict,
        t1w_identifier: dict,
        t2w_identifier: dict,
        bids_validate: bool = True,
    ) -> None:
        """
        bids_validate : bool, optional
            Whether to validate *bids_dir*`s compatibility with the BIDS format,
            by default True
        Parameters
        ----------
        bids_dir : Union[BIDSLayout, Path, str]
            Either BIDSLayout or path-like object representing an existing
            BIDS-compatible dataset
        participant_label : str
            String representing a subject existing within *bids_dir*
        dwi_identifier : dict
            dwi data type identifiers (by BIDS entities) dictionary
        fmap_identifier : dict
            fmap data type (by BIDS entities) dictionary
        t1w_identifier : dict
            t1w data type (by BIDS entities) dictionary
        t2w_identifier : dict
            t1w data type (by BIDS entities) dictionary
        bids_validate : bool, optional
            Whether to validate *bids_dir*`s compatibility with the BIDS format,
            by default True
        """
        self.bids_dir = bids_dir
        self.participant_label = participant_label
        self.queries = self.set_queries(
            dwi_identifier, fmap_identifier, t1w_identifier, t2w_identifier
        )
        self.bids_validate = bids_validate

    def set_queries(
        self,
        dwi_identifier: dict,
        fmap_identifier: dict,
        t1w_identifier: dict,
        t2w_identifier: dict,
    ) -> dict:
        """
        Combines both user-specified and basic identifications
        of different data types into a single dictionary.

        Parameters
        ----------
        dwi_identifier : dict
            dwi data type identifiers (by BIDS entities) dictionary
        fmap_identifier : dict
            fmap data type (by BIDS entities) dictionary
        t1w_identifier : dict
            t1w data type (by BIDS entities) dictionary
        t2w_identifier : dict
            t1w data type (by BIDS entities) dictionary

        Returns
        -------
        dict
            All data types and their corresponding identifiers
        """
        queries = {
            "dwi": {**self.DWI_QUERY, **dwi_identifier},
            "fmap": {**self.FMAP_QUERY, **fmap_identifier},
            "t1w": {**self.T1W_QUERY, **t1w_identifier},
            "t2w": {**self.T2W_QUERY, **t2w_identifier},
        }
        return queries

    def get_layout(self) -> BIDSLayout:
        """
        Returns a BIDSLayout instance describing *self.bids_dir*

        Returns
        -------
        BIDSLayout
            A BIDSLayout instance describing *self.bids_dir*
        """
        if isinstance(self.bids_dir, BIDSLayout):
            layout = self.bids_dir
        else:
            layout = BIDSLayout(str(self.bids_dir), self.bids_validate)
        return layout

    def collect_data(
        self,
    ) -> Tuple[dict, BIDSLayout, dict]:
        """
        Collects processing-relevant files from a BIDS dataset.

        Returns
        -------
        tuple
            Required preprocessing data

        """

        subj_data = {
            dtype: sorted(
                self.layout.get(
                    return_type="file",
                    subject=self.participant_label,
                    extension=self.FILE_EXTENSIONS,
                    **query,
                )
            )
            for dtype, query in self.queries.items()
        }

        return subj_data

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
            pattern = self.ENTITY_PATTERN.format(key=key, value=value)
            valid.append(pattern in file_name)
        return all(valid)

    def get_associated(self, file_name: str) -> list[BIDSFile]:
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
        bids_file = self.layout.get_file(file_name)
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

    def parse_associated_files(self, associated_files: list) -> dict:
        """
        Parse all associated files (to a BIDS entity) by their corresponding extensions

        Parameters
        ----------
        associated_files : list
            A list of *BIDSFile* instances associated with the same BIDS entity

        Returns
        -------
        dict
            A dictionary with keys of extensions/file types and their correspodning files.
        """
        parsed_files = {}
        for file_name in associated_files:
            extension = file_name.get_entities().get("extension").strip(".")
            file_type = [
                key
                for key, value in self.FILE_TYPES_BY_EXTENSIONS.items()
                if extension in value
            ]
            if file_type:
                parsed_files[file_type[0]] = file_name.path
        return parsed_files

    @property
    def subj_data(self) -> dict:
        """
        Return subject's raw nifti files by their corresponding data types
        Returns
        -------
        dict
            subject's raw nifti files by their corresponding data types
        """
        return self.collect_data()

    @property
    def layout(self) -> BIDSLayout:
        """
        Returns a BIDSLayout instance describing *self.bids_dir*

        Returns
        -------
        BIDSLayout
            a BIDSLayout instance describing *self.bids_dir*
        """
        return self.get_layout()
