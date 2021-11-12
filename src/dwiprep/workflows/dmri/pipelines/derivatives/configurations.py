from dwiprep.workflows.dmri.pipelines.tensor_estimation.configurations import (
    OUTPUT_NODE_FIELDS,
)

NATIVE_TENSOR_METRICS = ["native_" + metric for metric in OUTPUT_NODE_FIELDS]
COREG_TENSOR_METRICS = ["coreg_" + metric for metric in OUTPUT_NODE_FIELDS]

INPUT_NODE_FIELDS = (
    NATIVE_TENSOR_METRICS
    + COREG_TENSOR_METRICS
    + [
        "source_file",
        "phasediff_file",
        "phasediff_json",
        "native_dwi_preproc_file",
        "native_dwi_preproc_json",
        "native_dwi_preproc_bvec",
        "native_dwi_preproc_bval",
        "native_epi_ref_file",
        "native_epi_ref_json",
        "epi_to_t1w_aff",
        "t1w_to_epi_aff",
        "coreg_dwi_preproc_file",
        "coreg_epi_ref_file",
    ]
)

PHASEDIFF_KWARGS = dict(
    datatype="fmap",
    space="orig",
    desc="phasediff",
    suffix="fieldmap",
    compress=True,
    dismiss_entities=["direction"],
)

NATIVE_DWI_PREPROC_KWARGS = dict(
    datatype="dwi",
    space="orig",
    desc="preproc",
    suffix="dwi",
    compress=None,
)
COREG_DWI_PREPROC_KWARGS = dict(
    datatype="dwi",
    space="anat",
    desc="preproc",
    suffix="dwi",
    compress=None,
)
NATIVE_SBREF_PREPROC_KWARGS = dict(
    datatype="dwi",
    space="orig",
    desc="preproc",
    suffix="epiref",
    compress=None,
)
COREG_SBREF_PREPROC_KWARGS = dict(
    datatype="dwi",
    space="anat",
    desc="preproc",
    suffix="epiref",
    compress=None,
)
EPI_TO_T1_AFF_KWARGS = dict(
    datatype="dwi",
    suffix="xfm",
    extension=".txt",
    to="T1w",
    compress=False,
)
EPI_TO_T1_AFF_KWARGS["from"] = "epiref"

T1_to_EPI_AFF_KWARGS = dict(
    datatype="dwi",
    suffix="xfm",
    extension=".txt",
    to="epiref",
    compress=False,
)
T1_to_EPI_AFF_KWARGS["from"] = "T1w"

NATIVE_TENSOR_KWARGS = dict(datatype="tensor", space="orig")
COREG_TENSOR_KWARGS = dict(datatype="tensor", space="anat")
