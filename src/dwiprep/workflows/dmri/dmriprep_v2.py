from nipype.pipeline.engine.workflows import Workflow
from dwiprep.utils.bids_query.bids_query import BidsQuery
import nipype.interfaces.io as nio
from dwiprep.interfaces.mrconvert import map_list_to_kwargs as mrconvert_map
from dwiprep.workflows.dmri.base import (
    connect_conversion_to_wf,
    connect_tensor_wf,
    init_mrconvert_node,
    init_preprocess_wf,
)
from dwiprep.utils.bids_query.utils import FILE_EXTENSIONS
from dwiprep.workflows.dmri.utils.messages import MISSING_ENTITY
from dwiprep.workflows.dmri.utils.utils import (
    MANDATORY_ENTITIES,
    RECOMMENDED_ENTITIES,
    check_opposite_phase_encoding,
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

    #: Basic output fields for BIDSDataGrabber
    BASIC_DATAGRABBER_OUTFIELDS = {
        "T1w": BASIC_MRCONVERT_INPUTS,
        "T2w": BASIC_MRCONVERT_INPUTS,
        "dwi": BASIC_MRCONVERT_INPUTS + DWI_MRCONVERT_INPUTS,
        "fmap": BASIC_MRCONVERT_INPUTS,
    }

    def __init__(self, bids_query: BidsQuery, participant_label: str) -> None:
        """[summary]"""
        self.participant_label = participant_label
        self.bids_query = bids_query

    def get_sessions(self):
        """
        Return all available sessions available for *self.participant_label*.

        Returns
        -------
        list
            List of sessions' ids that are associated with *self.participant_label*.
        """
        return self.bids_query.layout.get(
            return_type="id", target="session", subject=self.participant_label
        )

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
                return False
        return True

    def get_session_data(self, session: str = None) -> dict:
        """
        Return all session-related relevant data.

        Parameters
        ----------
        session : str, optional
            Session identifier, by default None

        Returns
        -------
        dict
            Dictionary of session-related data
        """
        kwargs = {
            "return_type": "file",
            "subject": self.participant_label,
        }
        if session is not None:
            kwargs["session"] = session
        return {
            dtype: sorted(
                self.bids_query.layout.get(
                    **kwargs,
                    **query,
                )
            )
            for dtype, query in self.bids_query.queries.items()
        }

    def map_session_data_to_mrconvert_kwargs(
        self, session_id: str = None
    ) -> dict:
        """
        Map file names to their appropriate kwarg in *MRConvert* function.

        Parameters
        ----------
        session_id : str, optional
            Session identification, by default None

        Returns
        -------
        dict
            Dictionary with keys that are keyword arguments of *MRConvert*
        """
        mapped_data = {}
        for data_type, file_names in self.get_session_data(session_id).items():
            mapped_data[data_type] = mrconvert_map(file_names)
        return mapped_data

    def get_mif_conversion_nodes(self, session_id: str = None) -> dict:
        """
        Generate *MRConvert*-based nodes with appropriate inputs for different data types.

        Parameters
        ----------
        session_id : str, optional
            Session identifier, by default None

        Returns
        -------
        dict
            A dictionary of data types and their corresponding nodes.
        """
        mif_conversion_nodes = {}
        for data_type, kwargs in self.map_session_data_to_mrconvert_kwargs(
            session_id
        ).items():
            mif_conversion_nodes[data_type] = init_mrconvert_node(
                data_type, kwargs
            )
        return mif_conversion_nodes

    def build_workflow(self, mif_data: dict) -> Workflow:
        """
        Instanciates the initial cleaning workflow with *mif_data* as starting point.

        Parameters
        ----------
        mif_data : dict
            A dictionary of nodes for conversion of NIfTI to mif format.

        Returns
        -------
        Workflow
            An instanciated workflow for preprocessing of specific session.
        """
        wf = init_preprocess_wf()
        wf = connect_conversion_to_wf(mif_data, wf)
        wf = connect_tensor_wf(wf)
        return wf

    def validate_fieldmaps(self, session_data: dict):
        """
        Validates some preprocessing steps that rely on fieldmaps and their opposite phase encoding direction.

        Parameters
        ----------
        session_data : dict
            A dictionary of session's data

        Returns
        -------
        bool
            Whether to extract B0 image and run SDC.
        """
        if self.validate_session(session_data):
            fmap = session_data.get("fmap")
            dwi = session_data.get("dwi")
            extract_b0, run_sdc = check_opposite_phase_encoding(
                self.bids_query.layout, fmap, dwi
            )
        else:
            extract_b0 = False
            run_sdc = False
        return extract_b0, run_sdc

    @property
    def sessions(self):
        """
        All available sessions available for *self.participant_label*.

        Returns
        -------
        list
            Sessions' ids that are associated with *self.participant_label*.
        """
        return self.get_sessions()
