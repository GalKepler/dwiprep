# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
#
# Copyright 2021 The NiPreps Developers <nipreps@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# We support and encourage derived works from this project, please read
# about our expectations at
#
#     https://www.nipreps.org/community/licensing/
#
"""Orchestrating the dMRI-preprocessing workflow."""
from bids.layout.layout import BIDSLayout
from bids.layout.models import BIDSFile
from pathlib import Path
from nipype.pipeline import engine as pe
from nipype.interfaces import utility as niu
from nipype.pipeline.engine import workflows

from niworkflows.engine.workflows import LiterateWorkflow as Workflow
from dwiprep.interfaces.dds import DerivativesDataSink
from niworkflows.workflows.epi.refmap import init_epi_reference_wf

from dwiprep.workflows.dmri.pipelines import conversions


def get_fieldmaps(dwi_file: str, layout: BIDSLayout):
    """
    Locates all fieldmap associated with *dwi_file* according to the *IntendedFor* field in their corresponding jsons.

    Parameters
    ----------
    dwi_file : str
        dwi NIfTI file
    layout : BIDSLayout
        BIDSLayout instance for the queried bids directory.
    """
    fieldmaps = {}
    dwi_entities = layout.parse_file_entities(dwi_file)
    subject, session = [
        dwi_entities.get(key) for key in ["subject", "session"]
    ]
    available_fieldmaps = layout.get(
        subject=subject,
        session=session,
        datatype="fmap",
        extension=["nii", "nii.gz"],
    )
    target = Path(dwi_file).name
    for fmap in available_fieldmaps:
        intended_for = fmap.get_metadata().get("IntendedFor")
        if isinstance(intended_for, str):
            intended_for = [intended_for]
        intended_for = [Path(f).name for f in intended_for]
        if target in intended_for:
            fmap_dict = add_fieldmap(fmap, layout)
            for key, value in fmap_dict.items():
                fieldmaps[key] = value
    return fieldmaps


def add_fieldmap(fieldmap: BIDSFile, layout: BIDSLayout) -> dict:
    """
    Locates fieldmap-related json file and adds them in an appropriate dictionary with keys that describe their directionality

    Parameters
    ----------
    fieldmap : BIDSFile
        Fieldmap's NIfTI
    layout : BIDSLayout
        BIDSLayout instance for the queried bids directory.

    Returns
    -------
    dict
        Dictionary of fieldmap's NIfTI and json with appropriate keys.
    """
    entities = fieldmap.get_entities()
    entities.pop("fmap")
    direction = entities.get("direction")
    entities["extension"] = "json"
    json = layout.get(**entities)
    fieldmap_dict = {f"fmap_{direction}": fieldmap.path}
    if json:
        fieldmap_dict[f"fmap_{direction}_json"] = json[0].path
    return fieldmap_dict


def init_dwi_preproc_wf(
    dwi_file, layout: BIDSLayout = None, output_dir=None, work_dir=None
):
    """
    Build a preprocessing workflow for one DWI run.

    Workflow Graph
        .. workflow::
            :graph2use: orig
            :simple_form: yes

            from dmriprep.config.testing import mock_config
            from dmriprep import config
            from dmriprep.workflows.dwi.base import init_dwi_preproc_wf
            with mock_config():
                wf = init_dwi_preproc_wf(
                    f"{config.execution.layout.root}/"
                    "sub-THP0005/dwi/sub-THP0005_dwi.nii.gz"
                )

    Parameters
    ----------
    dwi_file : :obj:`os.PathLike`
        One diffusion MRI dataset to be processed.
    has_fieldmap : :obj:`bool`
        Build the workflow with a path to register a fieldmap to the DWI.

    Inputs
    ------
    dwi_file
        dwi NIfTI file
    in_bvec
        File path of the b-vectors
    in_bval
        File path of the b-values
    fmap
        File path of the fieldmap
    fmap_ref
        File path of the fieldmap reference
    fmap_coeff
        File path of the fieldmap coefficients
    fmap_mask
        File path of the fieldmap mask
    fmap_id
        The BIDS modality label of the fieldmap being used

    Outputs
    -------
    dwi_reference
        A 3D :math:`b = 0` reference, before susceptibility distortion correction.
    dwi_mask
        A 3D, binary mask of the ``dwi_reference`` above.
    gradients_rasb
        A *RASb* (RAS+ coordinates, scaled b-values, normalized b-vectors, BIDS-compatible)
        gradient table.

    See Also
    --------
    * :py:func:`~dmriprep.workflows.dwi.outputs.init_dwi_derivatives_wf`
    * :py:func:`~dmriprep.workflows.dwi.outputs.init_reportlets_wf`

    """
    from niworkflows.interfaces.reportlets.registration import (
        SimpleBeforeAfterRPT as SimpleBeforeAfter,
    )
    from dwiprep.workflows.dmri.pipelines.conversions import init_conversion_wf
    from dwiprep.workflows.dmri.pipelines.epi_ref import init_epi_ref_wf
    from dwiprep.workflows.dmri.pipelines.fmap_prep import (
        init_phasediff_wf,
        add_fieldmaps_to_wf,
    )
    from dwiprep.workflows.dmri.pipelines.preprocess import init_preprocess_wf

    # from dmriprep.workflows.dwi.outputs import (
    #     init_dwi_derivatives_wf,
    #     init_reportlets_wf,
    # )

    dwi_file = Path(dwi_file)

    # Build workflow
    workflow = Workflow(name=_get_wf_name(dwi_file.name))

    inputnode = pe.Node(
        niu.IdentityInterface(
            fields=[
                # DWI
                "dwi",
                "in_bvec",
                "in_bval",
                "in_json",
                # fmap
                "fmap_ap",
                "fmap_ap_json",
                "fmap_pa",
                "fmap_pa_json",
            ]
        ),
        name="inputnode",
    )

    # set inputs
    json_file = [
        j
        for j in layout.get_file(dwi_file).get_associations()
        if j.get_entities().get("extension") in [".json", "json"]
    ]
    json_file = json_file[0].path if json_file else None
    inputnode.inputs.dwi_file = str(dwi_file.absolute())
    inputnode.inputs.in_bvec = str(layout.get_bvec(dwi_file))
    inputnode.inputs.in_bval = str(layout.get_bval(dwi_file))
    inputnode.inputs.in_json = str(json_file)

    # add fieldmaps
    fieldmaps = get_fieldmaps(str(dwi_file), layout)
    for key, value in fieldmaps.items():
        inputnode.set_input(key, value)

    conversion_wf = init_conversion_wf()
    workflow.connect(
        [
            (
                inputnode,
                conversion_wf,
                [
                    ("dwi_file", "inputnode.dwi_file"),
                    ("in_bvec", "inputnode.in_bvec"),
                    ("in_bval", "inputnode.in_bval"),
                    ("in_json", "inputnode.dwi_json"),
                    ("fmap_ap", "inputnode.fmap_ap"),
                    ("fmap_ap_json", "inputnode.fmap_ap_json"),
                    ("fmap_pa", "inputnode.fmap_pa"),
                    ("fmap_pa_json", "inputnode.fmap_pa_json"),
                ],
            )
        ]
    )
    epi_ref_wf = init_epi_ref_wf()
    workflow.connect(
        [
            (
                conversion_wf,
                epi_ref_wf,
                [("outputnode.dwi_file", "inputnode.dwi_file")],
            )
        ]
    )
    phasediff_wf = init_phasediff_wf()
    phasediff_entry = add_fieldmaps_to_wf(
        inputnode, conversion_wf, epi_ref_wf, phasediff_wf
    )
    workflow.connect(phasediff_entry)
    preprocess_wf = init_preprocess_wf()
    workflow.connect(
        [
            (
                conversion_wf,
                preprocess_wf,
                [("outputnode.dwi_file", "inputnode.dwi_file")],
            ),
            (
                phasediff_wf,
                preprocess_wf,
                [
                    (
                        "outputnode.merged_phasediff",
                        "inputnode.merged_phasediff",
                    )
                ],
            ),
        ]
    )
    preproc_derivatives_node = pe.Node(
        DerivativesDataSink(
            base_directory=output_dir,
            space="dwi",
            desc="preproc",
            extension="mif",
        ),
        name="sinker",
    )
    workflow.connect(
        [
            (
                inputnode,
                preproc_derivatives_node,
                [("dwi_file", "source_file")],
            ),
            (
                preprocess_wf,
                preproc_derivatives_node,
                [("outputnode.dwi_preproc", "in_file")],
            ),
        ]
    )
    return inputnode, workflow
    # outputnode = pe.Node(
    #     niu.IdentityInterface(
    #         fields=["dwi_reference", "dwi_mask", "gradients_rasb"]
    #     ),
    #     name="outputnode",
    # )

    # dwi_reference_wf = init_epi_reference_wf(
    #     omp_nthreads=config.nipype.omp_nthreads,
    #     name="dwi_reference_wf",
    # )

    # brainextraction_wf = init_brainextraction_wf()
    # dwi_derivatives_wf = init_dwi_derivatives_wf(
    #     output_dir=str(config.execution.output_dir)
    # )

    # # If has_fieldmaps this will hold the corrected reference, original otherwise
    # buffernode = pe.Node(
    #     niu.IdentityInterface(fields=["dwi_reference", "dwi_mask"]),
    #     name="buffernode",
    # )

    # # MAIN WORKFLOW STRUCTURE
    # # fmt: off
    # workflow.connect([
    #     (inputnode, dwi_derivatives_wf, [("dwi_file", "inputnode.source_file")]),
    #     (inputnode, dwi_reference_wf, [(("dwi_file", _aslist), "inputnode.in_files")]),
    #     (dwi_reference_wf, brainextraction_wf, [
    #         ("outputnode.epi_ref_file", "inputnode.in_file")]),
    #     (gradient_table, dwi_reference_wf, [(("b0_mask", _aslist), "inputnode.t_masks")]),
    #     (buffernode, dwi_derivatives_wf, [
    #         ("dwi_reference", "inputnode.dwi_ref"),
    #         ("dwi_mask", "inputnode.dwi_mask"),
    #     ]),
    #     (buffernode, outputnode, [("dwi_reference", "dwi_reference"),
    #                               ("dwi_mask", "dwi_mask")]),
    #     (gradient_table, outputnode, [("out_rasb", "gradients_rasb")]),
    # ])
    # fmt: on
    # if config.workflow.run_reconall:
    #     from niworkflows.interfaces.nibabel import ApplyMask
    #     from niworkflows.anat.coregistration import init_bbreg_wf
    #     from ...utils.misc import sub_prefix as _prefix

    #     # Mask the T1w
    #     t1w_brain = pe.Node(ApplyMask(), name="t1w_brain")

    #     bbr_wf = init_bbreg_wf(
    #         debug=config.execution.debug,
    #         epi2t1w_init=config.workflow.dwi2t1w_init,
    #         omp_nthreads=config.nipype.omp_nthreads,
    #     )

    #     ds_report_reg = pe.Node(
    #         DerivativesDataSink(
    #             base_directory=str(config.execution.output_dir),
    #             datatype="figures",
    #         ),
    #         name="ds_report_reg",
    #         run_without_submitting=True,
    #     )

    #     def _bold_reg_suffix(fallback):
    #         return "coreg" if fallback else "bbregister"

    #     # fmt: off
    #     workflow.connect([
    #         (inputnode, bbr_wf, [
    #             ("fsnative2t1w_xfm", "inputnode.fsnative2t1w_xfm"),
    #             (("subject_id", _prefix), "inputnode.subject_id"),
    #             ("subjects_dir", "inputnode.subjects_dir"),
    #         ]),
    #         # T1w Mask
    #         (inputnode, t1w_brain, [("t1w_preproc", "in_file"),
    #                                 ("t1w_mask", "in_mask")]),
    #         (inputnode, ds_report_reg, [("dwi_file", "source_file")]),
    #         # BBRegister
    #         (buffernode, bbr_wf, [("dwi_reference", "inputnode.in_file")]),
    #         (bbr_wf, ds_report_reg, [
    #             ("outputnode.out_report", "in_file"),
    #             (("outputnode.fallback", _bold_reg_suffix), "desc")]),
    #     ])
    # fmt: on
    return inputnode, fieldmaps

    # if "eddy" not in config.workflow.ignore:
    #     # Eddy distortion correction
    #     eddy_wf = init_eddy_wf(debug=config.execution.debug)
    #     eddy_wf.inputs.inputnode.metadata = layout.get_metadata(str(dwi_file))

    #     ds_report_eddy = pe.Node(
    #         DerivativesDataSink(
    #             base_directory=str(config.execution.output_dir),
    #             desc="eddy",
    #             datatype="figures",
    #         ),
    #         name="ds_report_eddy",
    #         run_without_submitting=True,
    #     )

    #     eddy_report = pe.Node(
    #         SimpleBeforeAfter(
    #             before_label="Distorted",
    #             after_label="Eddy Corrected",
    #         ),
    #         name="eddy_report",
    #         mem_gb=0.1,
    #     )

    #     # fmt:off
    #     workflow.connect([
    #         (inputnode, eddy_wf, [("dwi_file", "inputnode.dwi_file"),
    #                               ("in_bvec", "inputnode.in_bvec"),
    #                               ("in_bval", "inputnode.in_bval")]),
    #         (inputnode, ds_report_eddy, [("dwi_file", "source_file")]),
    #         (brainextraction_wf, eddy_wf, [("outputnode.out_mask", "inputnode.dwi_mask")]),
    #         (brainextraction_wf, eddy_report, [("outputnode.out_file", "before")]),
    #         (eddy_wf, eddy_report, [("outputnode.eddy_ref_image", "after")]),
    #         (eddy_report, ds_report_eddy, [("out_report", "in_file")]),
    #     ])
    #     # fmt:on

    # # REPORTING ############################################################
    # reportlets_wf = init_reportlets_wf(
    #     str(config.execution.output_dir),
    #     sdc_report=has_fieldmap,
    # )
    # # fmt: off
    # workflow.connect([
    #     (inputnode, reportlets_wf, [("dwi_file", "inputnode.source_file")]),
    #     (dwi_reference_wf, reportlets_wf, [
    #         ("outputnode.validation_report", "inputnode.validation_report"),
    #     ]),
    #     (outputnode, reportlets_wf, [
    #         ("dwi_reference", "inputnode.dwi_ref"),
    #         ("dwi_mask", "inputnode.dwi_mask"),
    #     ]),
    # ])
    # # fmt: on

    # if not has_fieldmap:
    #     # fmt: off
    #     workflow.connect([
    #         (brainextraction_wf, buffernode, [
    #             ("outputnode.out_file", "dwi_reference"),
    #             ("outputnode.out_mask", "dwi_mask"),
    #         ]),
    #     ])
    #     # fmt: on
    #     return workflow

    # from niworkflows.interfaces.utility import KeySelect
    # from sdcflows.workflows.apply.registration import init_coeff2epi_wf
    # from sdcflows.workflows.apply.correction import init_unwarp_wf

    # coeff2epi_wf = init_coeff2epi_wf(
    #     debug=config.execution.debug,
    #     omp_nthreads=config.nipype.omp_nthreads,
    #     write_coeff=True,
    # )
    # unwarp_wf = init_unwarp_wf(
    #     debug=config.execution.debug, omp_nthreads=config.nipype.omp_nthreads
    # )
    # unwarp_wf.inputs.inputnode.metadata = layout.get_metadata(str(dwi_file))

    # output_select = pe.Node(
    #     KeySelect(fields=["fmap", "fmap_ref", "fmap_coeff", "fmap_mask"]),
    #     name="output_select",
    #     run_without_submitting=True,
    # )
    # output_select.inputs.key = estimator_key[0]
    # if len(estimator_key) > 1:
    #     config.loggers.workflow.warning(
    #         f"Several fieldmaps <{', '.join(estimator_key)}> are "
    #         f"'IntendedFor' <{dwi_file}>, using {estimator_key[0]}"
    #     )

    # sdc_report = pe.Node(
    #     SimpleBeforeAfter(
    #         before_label="Distorted",
    #         after_label="Corrected",
    #     ),
    #     name="sdc_report",
    #     mem_gb=0.1,
    # )

    # # fmt: off
    # workflow.connect([
    #     (inputnode, output_select, [("fmap", "fmap"),
    #                                 ("fmap_ref", "fmap_ref"),
    #                                 ("fmap_coeff", "fmap_coeff"),
    #                                 ("fmap_mask", "fmap_mask"),
    #                                 ("fmap_id", "keys")]),
    #     (output_select, coeff2epi_wf, [
    #         ("fmap_ref", "inputnode.fmap_ref"),
    #         ("fmap_coeff", "inputnode.fmap_coeff"),
    #         ("fmap_mask", "inputnode.fmap_mask")]),
    #     (dwi_reference_wf, coeff2epi_wf, [
    #         ("outputnode.epi_ref_file", "inputnode.target_ref")]),
    #     (dwi_reference_wf, unwarp_wf, [("outputnode.epi_ref_file", "inputnode.distorted")]),
    #     (coeff2epi_wf, unwarp_wf, [
    #         ("outputnode.fmap_coeff", "inputnode.fmap_coeff")]),
    #     (brainextraction_wf, sdc_report, [("outputnode.out_file", "before")]),
    #     (unwarp_wf, sdc_report, [("outputnode.corrected", "after"),
    #                              ("outputnode.corrected_mask", "wm_seg")]),
    #     (sdc_report, reportlets_wf, [("out_report", "inputnode.sdc_report")]),
    #     (unwarp_wf, buffernode, [("outputnode.corrected", "dwi_reference"),
    #                              ("outputnode.corrected_mask", "dwi_mask")]),
    # ])
    # # fmt: on

    # return workflow


def _get_wf_name(filename):
    """
    Derive the workflow name for supplied DWI file.

    Examples
    --------
    >>> _get_wf_name("/completely/made/up/path/sub-01_dir-AP_acq-64grad_dwi.nii.gz")
    'dwi_preproc_dir_AP_acq_64grad_wf'

    >>> _get_wf_name("/completely/made/up/path/sub-01_dir-RL_run-01_echo-1_dwi.nii.gz")
    'dwi_preproc_dir_RL_run_01_echo_1_wf'

    """
    from pathlib import Path

    fname = Path(filename).name.rpartition(".nii")[0].replace("_dwi", "_wf")
    fname_nosub = "_".join(fname.split("_")[1:])
    return f"dwi_preproc_{fname_nosub.replace('.', '_').replace(' ', '').replace('-', '_')}"


def _aslist(value):
    return [value]
