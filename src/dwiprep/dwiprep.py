"""Main module."""
from pathlib import Path
import os
import nipype.pipeline.engine as pe

from dwiprep.utils.bids_query.bids_query import BidsQuery
from dwiprep.workflows.dmri.dmriprep import DmriPrep

from smriprep.workflows.anatomical import init_anat_preproc_wf


class DmriPrepManager:
    #: Output directory name
    OUTPUT_NAME = "dmriprep"

    def __init__(
        self,
        bids_query: BidsQuery,
        destination: str,
        smriprep_kwargs: dict = {},
        fs_subjects_dir: str = None,
        work_dir: str = None,
    ) -> None:
        """[summary]"""
        self.bids_query = bids_query
        self.participant_labels = bids_query.participant_labels
        self.smriprep_kwargs = smriprep_kwargs
        self.destination = destination
        self.fs_subjects_dir = fs_subjects_dir or os.environ.get(
            "SUBJECTS_DIR"
        )
        self.work_dir = self.validate_work_dir(destination, work_dir)

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
        return workflow

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

    def preprocess_subjects(self):
        subjects_wf = {}
        for subject in self.participant_labels:
            wf = self.init_subject_wf(subject)
            wf.base_dir = self.work_dir
            anatomical_wf = self.init_anatomical_wf(subject)
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
                sessions_wfs += self.preprocess_session(
                    session_data,
                    subject,
                )
            for dmriprep_wf in sessions_wfs:
                self.connect_anatomical_and_diffusion(
                    wf, dmriprep_wf, anatomical_wf
                )
            subjects_wf[subject] = wf
        return subjects_wf
