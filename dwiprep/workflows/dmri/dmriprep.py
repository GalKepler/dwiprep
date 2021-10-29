import warnings
from typing import Union
from pathlib import Path
from bids import BIDSLayout
from dwiprep.workflows.dmri.utils.utils import (
    MANDATORY_ENTITIES,
    RECOMMENDED_ENTITIES,
)
from dwiprep.workflows.dmri.utils.messages import MISSING_ENTITY


class DmriPrep:
    #: Version
    __version__: "0.1.0"

    #: BIDS entities that are required for processing
    MANDATORY_ENTITIES = MANDATORY_ENTITIES

    #: BIDS entities that are recommended for processing
    RECOMMENDED_ENTITIES = RECOMMENDED_ENTITIES

    def __init__(
        self,
        subj_data: dict,
        destination: Union[Path, str],
        participant_label: str = None,
        run_kwargs: dict = None,
        work_dir: Path = None,
    ) -> None:
        """
        Initiates an DmriPrep instance.

        Parameters
        ----------
        subj_data : dict
            Paths to subject's processing-relevant files with corresponding keys.
        destination : Union[Path, str]
            Path to dmriprep's outputs
        participant_label : str, optional
            String identifying an existing subject in *bids_dir* (sub-xxx), by default None
        run_kwargs : dict, optional
            User-defined keyword arguments to be passed to *dmriprep* command , by default None
        work_dir : Path, optional
           Path where intermediate results should be stored , by default None
        """
        self.raw_data = self.validate_subject_data(subj_data)
        self.destination = Path(destination)
        self.participant_label = participant_label
        self.work_dir = self.validate_working_directory(work_dir)

    def validate_subject_data(self, subj_data: dict):
        """
        Validates the existence of mandatory and recommended BIDS entites in *subj_data*.

        Parameters
        ----------
        subj_data : dict
            Paths to subject's processing-relevant files with corresponding keys.

        Returns
        -------
        subj_data
            Paths to subject's processing-relevant files with corresponding keys.

        Raises
        ------
        FileNotFoundError
            Raises an error if any of the mandatory entities is missing.
        """
        for mandatory_entity in self.MANDATORY_ENTITIES:
            if mandatory_entity not in subj_data:
                raise FileNotFoundError(
                    MISSING_ENTITY.format(key=mandatory_entity)
                    + "\nProcessing will not be conducted!"
                )
        for recommended_entity in self.RECOMMENDED_ENTITIES:
            if recommended_entity not in subj_data:
                warnings.warn(
                    MISSING_ENTITY.format(key=recommended_entity)
                    + "\nWe highly encourage using this entities for preprocessing."
                )
        return subj_data

    def validate_working_directory(self, work_dir: Path = None):
        """
        Validates the existence of *work_dir*, creates it otherwise.

        Parameters
        ----------
        work_dir : Path,optional
           Path where intermediate results should be stored , by default None

        Returns
        -------
        Path
            Path where intermediate results should be stored
        """
        work_dir = (
            work_dir
            if work_dir is not None
            else self.destination.parent / "work"
        )
        work_dir.mkdir(exist_ok=True)
        return work_dir
