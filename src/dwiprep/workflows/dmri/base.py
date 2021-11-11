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
from dwiprep.workflows.dmri.pipelines import epi_ref


def init_dwi_preproc_wf(
    dwi_file,
    inputnode: pe.Node,
    output_dir=None,
    work_dir=None,
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
    from niworkflows.interfaces.nibabel import ApplyMask
    from dmriprep.utils.misc import sub_prefix as _prefix
    from dwiprep.workflows.dmri.pipelines import (
        init_conversion_wf,
        init_nii_conversion_wf,
        init_epi_ref_wf,
        init_phasediff_wf,
        add_fieldmaps_to_wf,
        init_preprocess_wf,
        init_tensor_wf,
    )
    from dwiprep.workflows.coreg.pipelines import (
        init_epireg_wf,
        init_apply_transform,
    )

    # from dmriprep.workflows.dwi.outputs import (
    #     init_dwi_derivatives_wf,
    #     init_reportlets_wf,
    # )

    dwi_file = Path(dwi_file)
    output_dir = Path(output_dir)
    # Build workflow
    workflow = Workflow(name=_get_wf_name(dwi_file.name))
    workflow.base_dir = work_dir

    # convert to mif format
    conversion_wf = init_conversion_wf(inputnode)
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

    # extract mean b0
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

    # prepare for topup+eddy and infer phasediff type
    phasediff_wf = init_phasediff_wf()
    phasediff_entry = add_fieldmaps_to_wf(
        inputnode, conversion_wf, epi_ref_wf, phasediff_wf
    )
    workflow.connect(phasediff_entry)

    # preprocess - denoise, topup, eddy, bias correction
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

    # extract preprocessed mean b0
    # preproc_epi_ref_wf = init_epi_ref_wf(name="preprocessed_epi_ref_wf")
    preproc_epi_ref_wf = epi_ref_wf.clone(name="preprocessed_epi_ref_wf")
    workflow.connect(
        [
            (
                preprocess_wf,
                preproc_epi_ref_wf,
                [("outputnode.dwi_preproc", "inputnode.dwi_file")],
            )
        ]
    )

    # convert to NIfTI format
    nii_conversion_wf = init_nii_conversion_wf()
    workflow.connect(
        [
            (
                preprocess_wf,
                nii_conversion_wf,
                [("outputnode.dwi_preproc", "inputnode.dwi_file")],
            ),
            (
                preproc_epi_ref_wf,
                nii_conversion_wf,
                [("outputnode.epi_ref_file", "inputnode.epi_ref")],
            ),
        ]
    )

    # conform to BIDS derivatives format
    for orig_file in [
        "dwi_file",
        "dwi_bvec",
        "dwi_bval",
        "dwi_json",
        "epi_ref_file",
        "epi_ref_json",
    ]:
        if "dwi" in orig_file:
            suffix = "dwi"
        elif "epi_ref" in orig_file:
            suffix = "sbref"
        if "_file" in orig_file:
            compress = True
        else:
            compress = False
        dsink = pe.Node(
            DerivativesDataSink(
                base_directory=output_dir,
                space="dwi",
                desc="preproc",
                suffix=suffix,
                compress=compress,
                source_file=str(dwi_file.absolute()),
            ),
            name=f"ds_{orig_file}",
        )
        workflow.connect(
            [
                (
                    nii_conversion_wf,
                    dsink,
                    [(f"outputnode.{orig_file}", "in_file")],
                ),
            ]
        )
    tensor_wf, metrics = init_tensor_wf()
    workflow.connect(
        [
            (
                preprocess_wf,
                tensor_wf,
                [("outputnode.dwi_preproc", "inputnode.dwi_file")],
            ),
        ]
    )
    for metric in metrics:
        dsink = pe.Node(
            DerivativesDataSink(
                base_directory=output_dir,
                space="dwi",
                suffix=metric,
                datatype="tensor",
                extension="nii.gz",
                source_file=str(dwi_file.absolute()),
            ),
            name=f"ds_{metric}",
        )
        workflow.connect(
            [
                (
                    tensor_wf,
                    dsink,
                    [(f"outputnode.{metric}", "in_file")],
                ),
            ]
        )
    # Mask the T1w
    t1w_brain = pe.Node(ApplyMask(), name="t1w_brain")
    epi_reg_wf = init_epireg_wf()

    workflow.connect(
        [
            (
                inputnode,
                epi_reg_wf,
                [
                    ("t1w_preproc", "inputnode.t1w_head"),
                ],
            ),
            # T1w Mask
            (
                inputnode,
                t1w_brain,
                [("t1w_preproc", "in_file"), ("t1w_mask", "in_mask")],
            ),
            # T1w Brain
            (t1w_brain, epi_reg_wf, [("out_file", "inputnode.t1w_brain")]),
            # BBRegister
            (
                nii_conversion_wf,
                epi_reg_wf,
                [("outputnode.epi_ref_file", "inputnode.in_file")],
            ),
        ]
    )
    for output, origin, target in zip(
        ["epi_to_t1w_aff", "t1w_to_epi_aff"], ["epi", "T1w"], ["T1w", "epi"]
    ):
        dsink = pe.Node(
            DerivativesDataSink(
                base_directory=output_dir,
                dismiss_entities=["direction"],
                suffix="xfm",
                mode="image",
                extension="txt",
                to=target,
                source_file=str(dwi_file.absolute()),
            ),
            name=f"ds_{output}",
        )
        setattr(dsink.inputs, "from", origin)
        workflow.connect(
            [
                (epi_reg_wf, dsink, [(f"outputnode.{output}", "in_file")]),
            ]
        )
    dsink = pe.Node(
        DerivativesDataSink(
            base_directory=output_dir,
            suffix="sbref",
            space="T1w",
            extension="nii.gz",
            desc="preproc",
            source_file=str(dwi_file.absolute()),
        ),
        name=f"ds_epi_ref_to_T1w",
    )
    workflow.connect(
        [(epi_reg_wf, dsink, [("outputnode.epi_to_t1w", "in_file")])]
    )
    apply_transform_wf = init_apply_transform(metrics.copy())
    workflow.connect(
        [
            (
                nii_conversion_wf,
                apply_transform_wf,
                [("outputnode.dwi_file", "inputnode.dwi_file")],
            ),
            (
                epi_reg_wf,
                apply_transform_wf,
                [("outputnode.epi_to_t1w_aff", "inputnode.epi_to_t1w_aff")],
            ),
            (
                t1w_brain,
                apply_transform_wf,
                [("out_file", "inputnode.t1w_brain")],
            ),
        ]
    )
    dsink = pe.Node(
        DerivativesDataSink(
            base_directory=output_dir,
            space="T1w",
            desc="preproc",
            suffix="dwi",
            compress=True,
            source_file=str(dwi_file.absolute()),
        ),
        name=f"ds_transformed_dwi",
    )
    workflow.connect(
        [(apply_transform_wf, dsink, [("outputnode.dwi_file", "in_file")])]
    )
    for metric in metrics:

        dsink = pe.Node(
            DerivativesDataSink(
                base_directory=output_dir,
                space="T1w",
                suffix=metric,
                datatype="tensor",
                extension="nii.gz",
                compress=True,
                source_file=str(dwi_file.absolute()),
            ),
            name=f"ds_tranformed_{metric}",
        )
        workflow.connect(
            [
                (
                    tensor_wf,
                    apply_transform_wf,
                    [(f"outputnode.{metric}", f"inputnode.{metric}")],
                ),
                (
                    apply_transform_wf,
                    dsink,
                    [(f"outputnode.{metric}", "in_file")],
                ),
            ]
        )

    return workflow


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
