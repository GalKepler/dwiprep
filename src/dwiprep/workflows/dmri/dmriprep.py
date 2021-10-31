import warnings
from typing import Union
from pathlib import Path

import nipype.pipeline.engine as pe
from nipype.interfaces import mrtrix3 as mrt

from dwiprep.utils.bids_query.bids_query import BidsQuery
from dwiprep.workflows.dmri.pipelines.the_base import THE_BASE
from dwiprep.workflows.dmri.utils.utils import (
    MANDATORY_ENTITIES,
    RECOMMENDED_ENTITIES,
    RELEVANT_DATA_TYPES,
    WORK_DIR_NAME,
    OUTPUT_PATTERNS,
    OUTPUT_ENTITIES,
    infer_phase_encoding_direction,
)
from dwiprep.interfaces.mrconvert import (
    mrconvert_map_types_to_kwargs,
    mrconvert,
)
from dwiprep.workflows.dmri.pipelines import THE_BASE
from dwiprep.workflows.dmri.utils.messages import MISSING_ENTITY


class DmriPrep:
    #: Version
    __version__ = "0.1.0"

    #: BIDS entities that are required for processing
    MANDATORY_ENTITIES = MANDATORY_ENTITIES

    #: BIDS entities that are recommended for processing
    RECOMMENDED_ENTITIES = RECOMMENDED_ENTITIES

    #: Data types that are relevant for preprocessing of dMRI data
    RELEVANT_DATA_TYPES = RELEVANT_DATA_TYPES

    #: Name of working directory where intermidete files should be stored
    WORK_DIR_NAME = WORK_DIR_NAME

    #: Pattern of output files
    OUTPUT_PATTERNS = OUTPUT_PATTERNS

    #: Output descriptions (desc-*) BIDS label
    OUTPUT_ENTITIES = OUTPUT_ENTITIES

    def __init__(
        self,
        bids_query: BidsQuery,
        destination: Union[Path, str],
        participant_label: str,
        work_dir: Path = None,
        denoise_kwargs: dict = None,
        mrcat_kwargs: dict = None,
        dwifslprep_kwargs: dict = None,
        biascorrect_kwargs: dict = None,
        pipeline_generator: dict = THE_BASE,
    ) -> None:
        """
        Initiates an DmriPrep instance.

        Parameters
        ----------
        subj_data : dict
            Paths to subject's processing-relevant files with corresponding keys.
        bids_query: BidsQuery
            BidsQuery instance for querying a BIDS-compatible dataset.
        destination : Union[Path, str]
            Path to dmriprep's outputs
        participant_label : str
            String identifying an existing subject in *bids_dir* (sub-xxx)
        run_kwargs : dict, optional
            User-defined keyword arguments to be passed to *dmriprep* command , by default None
        work_dir : Path, optional
           Path where intermediate results should be stored , by default None
        """
        self.raw_data = self.validate_subject_data(
            bids_query.subjects_data.get(participant_label)
        )
        self.bids_query = bids_query
        self.layout = bids_query.layout
        self.participant_label = participant_label
        self.destination = Path(destination)
        self.work_dir = self.validate_working_directory(work_dir)
        self.pipeline_generator = self.update_kwargs(
            pipeline_generator,
            denoise_kwargs,
            mrcat_kwargs,
            dwifslprep_kwargs,
            biascorrect_kwargs,
        )

    def update_kwargs(
        self,
        pipeline_generator: dict,
        denoise_kwargs: dict = None,
        mrcat_kwargs: dict = None,
        dwifslprep_kwargs: dict = None,
        biascorrect_kwargs: dict = None,
    ) -> pe.Workflow:
        """
        Instantiate a *pe.Workflow* instance with nodes as specified in *generator* and user-specified kwargs.
        Parameters
        ----------
        pipeline_geneator : dict
            A dictionary with keys of *nodes*,*kwargs* and their connections stated as *pipeline*.
        denoise_kwargs : dict, optional
            Keyword arguments for *dwidenoise*, by default None
        mrcat_kwargs : dict, optional
            Keyword arguments for *mrcat*, by default None
        dwifslprep_kwargs : dict, optional
            Keyword arguments for *dwifslpreproc*, by default None
        biascorrect_kwargs : dict, optional
            Keyword arguments for *dwibiascorrect*, by default None

        Returns
        -------
        pe.Workflow
            A connected template of *pe.Workflow* as stated in *pipeline_generator*
        """
        pipeline_kwargs = pipeline_generator.get("kwargs")
        for node, node_kwargs in zip(
            ["denoise", "concatenate", "preproc", "bias_correct"],
            [
                denoise_kwargs,
                mrcat_kwargs,
                dwifslprep_kwargs,
                biascorrect_kwargs,
            ],
        ):
            if isinstance(node_kwargs, dict):
                for key, value in node_kwargs:
                    pipeline_kwargs[node][key] = value
        pipeline_generator["kwargs"] = pipeline_kwargs
        return self.update_pipeline(pipeline_generator)

    def update_pipeline(self, pipeline_generator: dict) -> None:
        """
        Update pipeline upon adding user-defined kwargs
        """
        for node, kwargs in pipeline_generator.get("kwargs").items():
            for key, value in kwargs.items():
                pipeline_generator["nodes"][node].set_input(key, value)
        return pipeline_generator

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
            work_dir / self.WORK_DIR_NAME
            if work_dir is not None
            else self.destination.parent / "work" / self.WORK_DIR_NAME
        )
        work_dir.mkdir(exist_ok=True, parents=True)
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

    def map_subject_data_by_sessions(self) -> dict:
        """
        Rearrange subject's data so that data types and their corresponding files will be associated with specific sessions.

        Returns
        -------
        dict
            Dictionary with keys of sessions and their corresponding data.
        """
        data_by_sessions = {}
        if self.sessions:
            for session in self.sessions:
                data_by_sessions[session] = self.get_session_data(session)
        else:
            data_by_sessions["ses-1"] = data_by_sessions
        return data_by_sessions

    def build_output_name(
        self,
        key: str,
        in_file: Union[Path, str] = None,
        base_entities: dict = None,
    ) -> str:
        """
        Build BIDS-compatible output file name.

        Parameters
        ----------
        key : str
            Key corresponding to an entities dictionary in *self.OUTPUT_ENTITIES*
        in_file : Union[Path,str], optional
            Path-like object representing a file, by default None
        base_entities : dict, optional
            Basic entities for path construction. Only relevant if *in_file* is missing., by default None

        Returns
        -------
        str
            A BIDS-compatible name for *in_file*'s derivative.
        """
        entities = (
            self.layout.parse_file_entities(in_file)
            if in_file
            else base_entities
        )

        for key, value in self.OUTPUT_ENTITIES.get(key).items():
            entities[key] = value
        return (
            self.layout.build_path(
                entities,
                self.OUTPUT_PATTERNS,
                validate=False,
                absolute_paths=False,
            ),
            entities,
        )

    def convert_file_to_mif(
        self, in_file: Union[Path, str], session: str = None
    ) -> mrt.MRConvert:
        """
        Build an initiated *MRConvert* instance with relevant kwargs.

        Parameters
        ----------
        in_file : Union[Path,str]
            NIfTI file to be converted to mif format
        session : str, optional
            Session ID (needed for path construction), by default None

        Returns
        -------
        mrt.MRConvert
            An initiated MRConvert instance.
        """
        associated_files = self.bids_query.get_associated(in_file)
        out_fname, entities = self.build_output_name("raw_mif", in_file)
        output = self.destination / f"{out_fname.split('.')[0]}.mif"
        if output.exists():
            return output
        output.parent.mkdir(exist_ok=True, parents=True)
        parsed_files = self.bids_query.parse_associated_files(associated_files)
        kwargs = mrconvert_map_types_to_kwargs(parsed_files)
        kwargs["out_file"] = output
        mrconvert(kwargs).run()
        return output

    def convert_session_to_mif(self, session_data: dict) -> dict:
        """
        Converts an entire session to .mif format for better compatability with *mrtrix3*`s tools.

        Parameters
        ----------
        session_data : dict
            Dictionary of session-relevant files.

        Returns
        -------
        dict
            Dictionary of locations for converted files in .mif format.
        """
        mif_dict = {}
        for key, value in session_data.items():
            if isinstance(value, list):
                mif_dict[key] = [
                    self.convert_file_to_mif(val, key) for val in value
                ]
            else:
                mif_dict[key] = self.convert_file_to_mif(value, key)

        return mif_dict

    def initiate_working_directory(self) -> dict:
        """
        Initiates a working directory containing all available and useful data for processing.

        Returns
        -------
        dict
            Path to subject's relevant data by data types.
        """
        mif_dict = {}
        for (
            session,
            session_data,
        ) in self.map_subject_data_by_sessions().items():
            mif_dict[session] = self.convert_session_to_mif(session_data)
        return mif_dict

    def infer_pe_for_preprocessing(self, session_data: dict):
        """
        Build the preprocessing pipeline provided with initial data.

        Returns
        -------
        dict
            *pipeline_generator* with updated *pe_dir* kwarg.
        """
        dwi_series = session_data.get("dwi")
        pipeline_generator = self.pipeline_generator.copy()
        preproc_node = pipeline_generator.get("nodes").get("preproc")
        preproc_node.inputs.pe_dir = infer_phase_encoding_direction(
            self.layout, dwi_series
        )
        return pipeline_generator

    @property
    def sessions(self) -> list:
        """
        Dataset's available sessions.

        Returns
        -------
        list
            A list of available session for *self.participant_label*
        """
        sessions = self.get_sessions()
        return sessions

    @property
    def data_by_sessions(self) -> dict:
        """
        Return subject's data by corresponding session

        Returns
        -------
        dict
            Dictionary with keys of subject's available sessions.
        """
        return self.map_subject_data_by_sessions()
