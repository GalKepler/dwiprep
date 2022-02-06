"""Main module."""
import os
from pathlib import Path
from typing import Any, Iterable, Union

import nipype.pipeline.engine as pe
from bids import BIDSLayout
from smriprep.workflows.anatomical import init_anat_preproc_wf

from dwiprep.utils.bids_query.bids_query import BidsQuery
from dwiprep.workflows import dmri
from dwiprep.workflows.dmri import dmriprep
from dwiprep.workflows.dmri.dmriprep import DmriPrep
from dwiprep.workflows.dmri.utils.utils import OUTPUTS


class DmriPrepManager:
    #: Output directory name
    OUTPUT_NAME = "dmriprep"
    #: SmriPrep output pattern.
    SMRIPREP_OUTPUT_PATTERN: str = (
        "{main_dir}/**/{sub_dir}/sub-{subject_id}_{session_id}_{output_id}"
    )

    #: FreeSurfer output pattern.
    FS_OUTPUT_PATTERN: str = "{main_dir}/sub-{subject_id}/**/*{output_id}"

    #: Session results pattern.
    SESSION_PATTERN: str = "dmriprep/sub-{subject_id}/ses-*"

    #: Expected outputs.
    OUTPUTS = OUTPUTS

    def __init__(
        self,
        bids_dir: Union[BIDSLayout, Path, str],
        destination: str,
        dwi_identifier: dict = {},
        fmap_identifier: dict = {},
        t1w_identifier: dict = {},
        t2w_identifier: dict = {},
        smriprep_kwargs: dict = {},
        participant_label: Union[str, list] = None,
        bids_validate: bool = True,
        fs_subjects_dir: str = None,
        work_dir: str = None,
    ) -> None:
        """[summary]"""
        self.bids_query = self.init_bids_query(
            bids_dir,
            dwi_identifier,
            fmap_identifier,
            t1w_identifier,
            t2w_identifier,
            participant_label,
            bids_validate,
        )
        self.smriprep_kwargs = smriprep_kwargs
        self.destination = destination
        self.fs_subjects_dir = fs_subjects_dir or os.environ.get(
            "SUBJECTS_DIR"
        )
        self.work_dir = self.validate_work_dir(destination, work_dir)

    def init_bids_query(
        self,
        bids_dir: Union[BIDSLayout, Path, str],
        dwi_identifier: dict = {},
        fmap_identifier: dict = {},
        t1w_identifier: dict = {},
        t2w_identifier: dict = {},
        participant_label: Union[str, list] = None,
        bids_validate: bool = True,
    ):
        """[summary]

        Parameters
        ----------
        bids_dir : Union[BIDSLayout, Path, str]
            [description]
        dwi_identifier : dict, optional
            [description], by default {}
        fmap_identifier : dict, optional
            [description], by default {}
        t1w_identifier : dict, optional
            [description], by default {}
        t2w_identifier : dict, optional
            [description], by default {}
        participant_label : Union[str, list], optional
            [description], by default None
        bids_validate : bool, optional
            [description], by default True
        """
        return BidsQuery(
            bids_dir,
            dwi_identifier,
            fmap_identifier,
            t1w_identifier,
            t2w_identifier,
            participant_label,
            bids_validate,
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

    def init_anatomical_wf(self, participant_label: str):
        subj_data = self.bids_query.collect_data(participant_label)
        t1w = [f.get("nifti") for f in subj_data.get("T1w")]
        t2w = [f.get("nifti") for f in subj_data.get("T2w")]

        anat_derivatives = self.smriprep_kwargs.get("anat_derivatives")
        spaces = self.smriprep_kwargs.get("spaces")
        if anat_derivatives:
            from smriprep.utils.bids import collect_derivatives

            std_spaces = spaces.get_spaces(nonstandard=False, dim=(3,))
            anat_derivatives = collect_derivatives(
                anat_derivatives.absolute(),
                participant_label,
                std_spaces,
                self.smriprep_kwargs.get("run_reconall"),
            )

        anat_preproc_wf = init_anat_preproc_wf(
            bids_root=self.bids_query.bids_dir,
            existing_derivatives=anat_derivatives,
            output_dir=str(self.destination),
            t1w=t1w,
            **self.smriprep_kwargs,
        )
        anat_preproc_wf.get_node("inputnode").inputs.subject_id = (
            "sub-" + participant_label
        )

        anat_preproc_wf.get_node("inputnode").inputs.t2w = t2w
        anat_preproc_wf.get_node("inputnode").inputs.t1w = t1w

        anat_preproc_wf.get_node(
            "inputnode"
        ).inputs.subjects_dir = self.fs_subjects_dir
        anat_preproc_wf.__desc__ = f"\n\n{anat_preproc_wf.__desc__}"
        # Overwrite ``out_path_base`` of smriprep's DataSinks
        for node in anat_preproc_wf.list_node_names():
            if node.split(".")[-1].startswith("ds_"):
                anat_preproc_wf.get_node(
                    node
                ).interface.out_path_base = "dmriprep"
        return anat_preproc_wf

    def init_subject_wf(self, participant_label: str):
        name = f"single_subject_{participant_label}_wf"
        workflow = pe.Workflow(name=name)
        return workflow, name

    def preprocess_session(self, session_data: dict, participant_label: str):
        dmriprep = DmriPrep(
            self.bids_query,
            session_data,
            participant_label,
            self.destination,
            self.work_dir,
        )
        dmri_wfs = dmriprep.init_workflow_per_dwi()

        return dmri_wfs

    def connect_anatomical_and_diffusion(
        self,
        subject_workflow: pe.Workflow,
        dwi_preproc_wf: pe.Workflow,
        anat_preproc_wf: pe.Workflow,
    ):
        subject_workflow.connect(
            [
                (
                    anat_preproc_wf,
                    dwi_preproc_wf,
                    [
                        ("outputnode.t1w_preproc", "inputnode.t1w_preproc"),
                        ("outputnode.t1w_mask", "inputnode.t1w_mask"),
                        ("outputnode.t1w_dseg", "inputnode.t1w_dseg"),
                        ("outputnode.t1w_aseg", "inputnode.t1w_aseg"),
                        ("outputnode.t1w_aparc", "inputnode.t1w_aparc"),
                        ("outputnode.t1w_tpms", "inputnode.t1w_tpms"),
                        ("outputnode.template", "inputnode.template"),
                        ("outputnode.anat2std_xfm", "inputnode.anat2std_xfm"),
                        ("outputnode.std2anat_xfm", "inputnode.std2anat_xfm"),
                        # Undefined if --fs-no-reconall, but this is safe
                        ("outputnode.subjects_dir", "inputnode.subjects_dir"),
                        (
                            "outputnode.t1w2fsnative_xfm",
                            "inputnode.t1w2fsnative_xfm",
                        ),
                        (
                            "outputnode.fsnative2t1w_xfm",
                            "inputnode.fsnative2t1w_xfm",
                        ),
                    ],
                ),
            ]
        )

    def run(self):
        for subject in self.participant_labels:
            wf, name = self.init_subject_wf(subject)
            wf_base_dir = f"{self.work_dir}/{name}"
            wf.base_dir = wf_base_dir
            # wf.base_dir = self.work_dir
            anatomical_wf = self.init_anatomical_wf(subject)
            # anatomical_wf.base_dir = wf_base_dir
            sessions = self.bids_query.get_sessions(subject)
            sessions_wfs = []
            sessions_data = (
                [
                    self.bids_query.collect_data(subject, session)
                    for session in sessions
                ]
                if sessions
                else [self.bids_query.collect_data(subject)]
            )
            for session_data in sessions_data:
                # wf, name = self.init_subject_wf(subject)
                # wf.base_dir = self.work_dir
                # anatomical_wf = self.init_anatomical_wf(subject)
                sessions_wfs += self.preprocess_session(
                    session_data,
                    subject,
                )
            for dmriprep_wf in sessions_wfs:
                # dmriprep_wf.base_dir = wf_base_dir
                self.connect_anatomical_and_diffusion(
                    wf, dmriprep_wf, anatomical_wf
                )
            wf.write_graph(graph2use="colored")
            wf.run()

    def generate_fs_outputs(
        self, main_dir: str, subject_id: str, output_id: str
    ) -> Iterable[Path]:
        """
        Generate FreeSurfer output paths.

        Parameters
        ----------
        main_dir : str
            Main output directory
        output_id : str
            Output file name pattern

        Yields
        -------
        Path
            Output paths
        """
        pattern = self.FS_OUTPUT_PATTERN.format(
            main_dir=main_dir, subject_id=subject_id, output_id=output_id
        )
        return Path(self.destination).absolute().rglob(pattern)

    def generate_smriprep_outputs(
        self,
        main_dir: str,
        sub_dir: str,
        subject_id: str,
        session_id: str,
        output_id: str,
    ) -> Iterable[Path]:
        """
        Generate smriprep output paths.

        Parameters
        ----------
        main_dir : str
            Main output directory
        sub_dir : str
            Results sub-directory name
        subject_id : str
            String subject ID
        session_id : str
            String session ID
        output_id : str
            Output file name pattern

        Yields
        -------
        Path
            Output paths
        """
        pattern = self.SMRIPREP_OUTPUT_PATTERN.format(
            main_dir=main_dir,
            sub_dir=sub_dir,
            subject_id=subject_id,
            session_id=session_id,
            output_id=output_id,
        )

        return Path(self.destination).absolute().rglob(pattern)

    def find_output(
        self, partial_output: str, subject_id: str, session_id: str
    ):
        """
        uses the destination and some default dictionary to locate specific
        output files of *smriprep*.

        Parameters
        ----------
        partial_output : str
            A string that identifies a specific output
        subject_id : str
            Subject string ID
        session_id : str
            Session string ID
        """
        main_dir, sub_dir, output_id = self.OUTPUTS.get(partial_output)
        if main_dir == "freesurfer":
            outputs = list(
                self.generate_fs_outputs(main_dir, subject_id, output_id)
            )
        elif main_dir == "dmriprep":
            outputs = list(
                self.generate_smriprep_outputs(
                    main_dir, sub_dir, subject_id, session_id, output_id
                )
            )
        # if len(outputs) == 1:
        #     return str(outputs[0])
        # elif len(outputs) > 1:
        if ("native" in partial_output) and (
            "transform" not in partial_output
        ):
            return [str(f) for f in outputs if ("MNI" not in f.name)]
        return [str(f) for f in outputs]

    def generate_output_dict(self) -> dict:
        """
        Generates a dictionary of the expected output file paths by key.

        Returns
        -------
        dict
            Output files by key
        """
        output_dict = {}
        subject_ids = self.participant_labels
        subject_ids = (
            subject_ids if isinstance(subject_ids, list) else [subject_ids]
        )
        for subject_id in subject_ids:
            output_dict[subject_id] = {}
            # session_pattern = self.SESSION_PATTERN.format(
            #     subject_id=subject_id
            # )
            for key in self.OUTPUTS:
                output_dict[subject_id][key] = self.find_output(
                    key, subject_id, "*"
                )
        if len(output_dict) == 1:
            return output_dict.get(subject_id)
        return output_dict

    @property
    def participant_labels(self) -> list:
        """
        Return available subjects from *self.layout* or given list of subjects.

        Returns
        -------
        list
            A list of subjects' identifiers available in *self.layout*
        """
        return self.bids_query.participant_labels
