from pathlib import Path
from typing import Tuple

import nipype.pipeline.engine as pe

from dwiprep.utils.bids_query.bids_query import BidsQuery
from dwiprep.utils.inputs import INPUTNODE
from dwiprep.utils.bids_query.utils import get_fieldmaps, add_fieldmap
from dwiprep.interfaces.mrconvert import (
    MAP_KWARGS_TO_SUFFIXES,
)
from dwiprep.workflows.dmri.utils.messages import MISSING_ENTITY
from dwiprep.workflows.dmri.utils.utils import (
    MANDATORY_ENTITIES,
    RECOMMENDED_ENTITIES,
)
from dwiprep.workflows.dmri.base import init_dwi_preproc_wf
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
    #: Scan-wise input node
    INPUTNODE = INPUTNODE

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
        self.session_data = session_data
        self.participant_label = participant_label
        self.session = session
        destination = Path(destination) / self.OUTPUT_NAME
        self.destination = destination
        self.work_dir = self.validate_work_dir(destination, work_dir)
        # self.work_dir, self.destination = self.set_destinations(
        #     destination, work_dir
        # )

    def infer_session(self, dwi: dict):
        """
        Attempt to infer session's id even if not given one.

        Parameters
        ----------
        dwi : dict
            A dictionary of dwi-related files (from a BIDS-compatible dataset)
        session : str, optional
            Session's identifier, by default None

        Returns
        -------
        str
            Session's identifer if available for *dwi*.
        """
        nifti = dwi.get("nifti")
        if not self.session:
            session = self.bids_query.layout.parse_file_entities(nifti).get(
                "session"
            )
            return session
        else:
            return self.session

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

    def data_to_input_node(self, run_data: str) -> pe.Node:
        """
        Generate a run-specific input node.

        Parameters
        ----------
        run_data : dict
            Run's DWI-related data.
        session : str, optional
            Session's identifier, by default None

        Returns
        -------
        pe.Node
            An input node.
        """
        inputnode = self.INPUTNODE
        dwi_nifti, dwi_json, dwi_bvec, dwi_bval = [
            run_data.get(key) for key in ["nifti", "json", "bvec", "bval"]
        ]
        if not all([run_data.values()]):
            raise FileNotFoundError(
                f"Could not found neccesary DWI-related files for subject {self.participant_label}."
            )
        inputnode.inputs.dwi_file = str(Path(dwi_nifti).absolute())
        inputnode.inputs.in_bvec = str(Path(dwi_bvec).absolute())
        inputnode.inputs.in_bval = str(Path(dwi_bval).absolute())
        inputnode.inputs.in_json = str(Path(dwi_json).absolute())

        # add fieldmaps
        fieldmaps = get_fieldmaps(str(dwi_nifti), self.bids_query.layout)
        for key, value in fieldmaps.items():
            inputnode.set_input(key, value)
        return inputnode

    def init_workflow_per_dwi(self):
        # self.validate_session(self.session_data)
        dmriprep_wfs = []
        for dwi_data in self.session_data.get("dwi"):
            inputnode = self.data_to_input_node(dwi_data)
            dmriprep_wf = init_dwi_preproc_wf(
                dwi_data.get("nifti"),
                inputnode,
                self.destination,
                self.work_dir,
            )
            dmriprep_wf.base_dir = self.work_dir
            for node in dmriprep_wf.list_node_names():
                if node.split(".")[-1].startswith("ds_"):
                    dmriprep_wf.get_node(
                        node
                    ).interface.out_path_base = "dmriprep"
            dmriprep_wfs.append(dmriprep_wf)
        return dmriprep_wfs
