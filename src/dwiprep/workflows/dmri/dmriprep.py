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
    __version__ = "0.1.0"

    #: BIDS entities that are required for processing
    MANDATORY_ENTITIES = MANDATORY_ENTITIES

    #: BIDS entities that are recommended for processing
    RECOMMENDED_ENTITIES = RECOMMENDED_ENTITIES

    def __init__(
        self,
        subj_data: dict,
        layout: BIDSLayout,
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
        layout: BIDSLayout
            Pybids' BIDSLayout instance for querying a BIDS-compatible dataset.
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
        self.layout = layout
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

    def get_sessions(self) -> list:
        """
        An easy wrapper around the *get_sessions* method of BIDSLayout
        to retrieve dataset's available sessions.

        Returns
        -------
        list
            A list of available session for *self.participant_label*.
        """
        return (
            self.layout.get_sessions()
            if self.participant_label is None
            else self.layout.get_sessions(subject=self.participant_label)
        )

    def get_session_data(self, session_id: str):
        """
        Query a BIDSLayout to locate all files (by their corresponding entities)
        related to session *session_id*

        Parameters
        ----------
        session_id : str
            String identifying a session in *self.layout*
        """
        session_dict = {}
        for entity, values in self.raw_data.items():
            session_dict[entity] = [
                val
                for val in values
                if self.layout.parse_file_entities(val).get("session")
                == session_id
            ]
            if len(session_dict[entity]) == 1:
                session_dict[entity] = session_dict[entity][0]
        return session_dict

    def arrange_subject_data_by_sessions(self) -> dict:
        """

        Returns
        -------
        dict
            [description]
        """
        data_by_sessions = {}
        for session in self.sessions:
            data_by_sessions[session] = self.get_session_data(session)
        return data_by_sessions
    
    @property
    def sessions(self) -> list:
        """
        Dataset's available sessions.

        Returns
        -------
        list
            A list of available session for *self.participant_label*
        """
        return self.get_sessions()
