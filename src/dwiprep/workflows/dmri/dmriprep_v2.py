from pathlib import Path
import nipype
from nipype.interfaces.utility import IdentityInterface
from nipype.pipeline.engine.workflows import Workflow
from dwiprep.utils.bids_query.bids_query import BidsQuery
import nipype.interfaces.io as nio
import nipype.pipeline.engine as pe
from dwiprep.interfaces.mrconvert import (
    MAP_KWARGS_TO_SUFFIXES,
    map_list_to_kwargs as mrconvert_map,
)
from dwiprep.workflows.dmri.base import (
    connect_conversion_to_wf,
    connect_tensor_wf,
    init_mrconvert_node,
    init_preprocess_wf,
    init_datagrabber,
    init_mrconvert_wf,
    get_inputnode,
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
        participant_label: str,
        destination: str,
        session: str = None,
        work_dir: str = None,
    ) -> None:
        """[summary]"""
        self.participant_label = participant_label
        self.session = session
        self.bids_query = bids_query
        self.destination = Path(destination) / self.OUTPUT_NAME
        self.work_dir = self.validate_work_dir(work_dir)

    def validate_work_dir(self, work_dir: str = None):
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
            else str(Path(self.destination).parent / "work")
        )

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

    def get_session_data(self) -> dict:
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
        if self.session is not None:
            kwargs["session"] = self.session
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
        self,
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
        for data_type, file_names in self.session_data.items():
            mapped_data[data_type] = mrconvert_map(
                file_names, self.MAP_KWARGS_TO_SUFFIXES
            )
        return mapped_data

    def get_mif_conversion_nodes(self) -> dict:
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
        for (
            data_type,
            kwargs,
        ) in self.map_session_data_to_mrconvert_kwargs().items():
            mif_conversion_nodes[data_type] = init_mrconvert_node(
                data_type, kwargs
            )
        return mif_conversion_nodes

    def build_data_grabber(self, session: str = None):
        """
        Generates a BIDSDataGrabber instance suited for specific subject/session

        Parameters
        ----------
        session : str
            Session identifier

        Returns
        -------
        BIDSDataGrabber
            A `BIDSDataGrabber` instance suited for specific subject/session
        """
        grabber = init_datagrabber(
            self.bids_query.bids_dir,
            self.participant_label,
            self.bids_query.queries,
            session,
        )
        return grabber

    def init_input_node(self):
        inputnode = get_inputnode()
        inputnode.inputs.dwi_file = self.session_data

    def init_conversion_wf(self, grabber: nio.BIDSDataGrabber):
        """
        Build data-type-specific workflows

        Parameters
        ----------
        grabber : nio.BIDSDataGrabber
            A `BIDSDataGrabber` instance suited for specific subject/session

        Returns
        -------
        dict
            datatype-specific mif conversion workflows
        """
        conversion_dict = {}
        for data_type in self.bids_query.queries:
            conversion_dict[data_type] = init_mrconvert_wf(
                data_type, grabber, self.MAP_KWARGS_TO_SUFFIXES
            )
        return conversion_dict

    def build_workflow(self, session: str = None) -> Workflow:
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
        work_dir, destination = self.set_destination(session)
        inputnode = self.build_data_grabber(session)
        conversion_wf = self.init_conversion_wf(inputnode)
        session_data = self.get_session_data(session)
        dwi, fmap = [session_data.get(key)[0] for key in ["dwi", "fmap"]]
        wf = init_preprocess_wf(
            self.bids_query.bids_dir,
            self.destination,
            dwi,
            fmap,
        )

        wf = connect_conversion_to_wf(conversion_wf, wf)
        wf = connect_tensor_wf(
            self.bids_query.bids_dir, self.destination, dwi, wf
        )
        wf.base_dir = work_dir
        return wf

    def set_destination(self, session: str = None):
        base_directory = Path(self.work_dir) / f"sub-{self.participant_label}"
        output_directory = (
            Path(self.destination) / f"sub-{self.participant_label}"
        )
        if session:
            base_directory = base_directory / f"ses-{session}"

            output_directory = output_directory / f"ses-{session}"
        return base_directory, output_directory

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

    def run_preprocessing(self):
        if self.sessions:
            for session in self.sessions:
                mif_conversion = self.get_mif_conversion_nodes(session)
                wf = self.build_workflow(mif_conversion, session)
        else:
            mif_conversion = self.get_mif_conversion_nodes()
            wf = self.build_workflow(mif_conversion)

    @property
    def session_data(self):
        return self.get_session_data()

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
