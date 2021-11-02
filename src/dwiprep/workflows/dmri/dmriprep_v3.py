from pathlib import Path
from typing import Tuple
from dwiprep.utils.bids_query.bids_query import BidsQuery
from dwiprep.interfaces.mrconvert import (
    MAP_KWARGS_TO_SUFFIXES,
)
from dwiprep.workflows.dmri.utils.messages import MISSING_ENTITY
from dwiprep.workflows.dmri.utils.utils import (
    MANDATORY_ENTITIES,
    RECOMMENDED_ENTITIES,
)

import warnings


class DmriPrep:
    #: BIDS entities that are required for processing
    MANDATORY_ENTITIES = MANDATORY_ENTITIES

    #: BIDS entities that are recommended for processing
    RECOMMENDED_ENTITIES = RECOMMENDED_ENTITIES

    #: Basic MRConvert inputs
    BASIC_MRCONVERT_INPUTS = ["in_file", "json_import"]

    #: DWI-related MRConvert inputs
    DWI_MRCONVERT_INPUTS = ["in_bvec", "in_bval"]
    #: Mapping of suffixes to mrconvert's kwargs
    MAP_KWARGS_TO_SUFFIXES = MAP_KWARGS_TO_SUFFIXES
    #: Basic output fields for BIDSDataGrabber
    BASIC_DATAGRABBER_OUTFIELDS = {
        "T1w": BASIC_MRCONVERT_INPUTS,
        "T2w": BASIC_MRCONVERT_INPUTS,
        "dwi": BASIC_MRCONVERT_INPUTS + DWI_MRCONVERT_INPUTS,
        "fmap": BASIC_MRCONVERT_INPUTS,
    }
    #: Output directory name
    OUTPUT_NAME = "dmriprep"

    def __init__(
        self,
        bids_query: BidsQuery,
        session_data: dict,
        participant_label: str,
        destination: str,
        session: str = None,
        work_dir: str = None,
    ) -> None:
        """[summary]"""
        self.bids_query = bids_query
        self.validate_session(session_data)
        self.participant_label = participant_label
        self.session = session
        destination = Path(destination) / self.OUTPUT_NAME
        self.work_dir, self.destination = self.set_destinations(
            destination, work_dir
        )

    def validate_work_dir(self, destination: str, work_dir: str = None):
        """
        Locates a working directory.

        Parameters
        ----------
        work_dir : str, optional
            Path tot working directory, by default None

        Returns
        -------
        str
            Path to working directory
        """
        return (
            work_dir
            if work_dir is not None
            else str(Path(destination).parent / "work")
        )

    def set_destinations(
        self, destination: str, work_dir: str = None
    ) -> Tuple[str, str]:
        """
        Set session/subject-speicifc working and destination directories

        Parameters
        ----------
        destination : str
            Path to pipeline's outputs
        work_dir : str, optional
            Path to pipeline's working directory, by default None

        Returns
        -------
        Tuple[str,str]
            Paths to subject/session-specific working an target directories.
        """
        work_dir = self.validate_work_dir(destination, work_dir)
        base_directory = Path(work_dir) / f"sub-{self.participant_label}"
        output_directory = Path(destination) / f"sub-{self.participant_label}"
        if self.session:
            base_directory = base_directory / f"ses-{self.session}"

            output_directory = output_directory / f"ses-{self.session}"
        return base_directory, output_directory

    def validate_session(self, session_data: dict) -> bool:
        """
        Validates the existence of mandatory and recommended BIDS entites in *subj_data*.

        Parameters
        ----------
        subj_data : dict
            Paths to subject's processing-relevant files with corresponding keys.

        Returns
        -------
        bool
            Whether there's a valid fieldmap entity in the session (i.e, run SDC)

        Raises
        ------
        FileNotFoundError
            Raises an error if any of the mandatory entities is missing.
        """

        for mandatory_entity in self.MANDATORY_ENTITIES:
            if mandatory_entity not in session_data:
                raise FileNotFoundError(
                    MISSING_ENTITY.format(key=mandatory_entity)
                    + "\nProcessing will not be conducted!"
                )
        for recommended_entity in self.RECOMMENDED_ENTITIES:
            if recommended_entity not in session_data:
                warnings.warn(
                    MISSING_ENTITY.format(key=recommended_entity)
                    + "\nWe highly encourage using this entities for preprocessing."
                )
