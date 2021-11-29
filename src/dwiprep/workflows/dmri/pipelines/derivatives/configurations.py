INPUT_NODE_FIELDS = [
    "source_file",
    "base_directory",
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
    "coreg_dwi_preproc_bvec",
    "coreg_dwi_preproc_bval",
    "coreg_dwi_preproc_json",
    "coreg_epi_ref_file",
    "native_tensor_metrics",
    "coreg_tensor_metrics",
]

PHASEDIFF_KWARGS = dict(
    datatype="fmap",
    space="orig",
    desc="phasediff",
    suffix="fieldmap",
    compress=None,
    dismiss_entities=["direction"],
    out_path_base="dmriprep",
)

NATIVE_DWI_PREPROC_KWARGS = dict(
    datatype="dwi",
    space="orig",
    desc="preproc",
    suffix="dwi",
    compress=None,
    out_path_base="dmriprep",
)
COREG_DWI_PREPROC_KWARGS = dict(
    datatype="dwi",
    space="anat",
    desc="preproc",
    suffix="dwi",
    compress=None,
    out_path_base="dmriprep",
)
NATIVE_SBREF_PREPROC_KWARGS = dict(
    datatype="dwi",
    space="orig",
    desc="preproc",
    suffix="epiref",
    compress=None,
    out_path_base="dmriprep",
)
COREG_SBREF_PREPROC_KWARGS = dict(
    datatype="dwi",
    space="anat",
    desc="preproc",
    suffix="epiref",
    compress=None,
    out_path_base="dmriprep",
)
EPI_TO_T1_AFF_KWARGS = dict(
    datatype="dwi",
    suffix="xfm",
    extension=".txt",
    to="T1w",
    compress=False,
    out_path_base="dmriprep",
)
EPI_TO_T1_AFF_KWARGS["from"] = "epiref"

T1_to_EPI_AFF_KWARGS = dict(
    datatype="dwi",
    suffix="xfm",
    extension=".txt",
    to="epiref",
    compress=False,
    out_path_base="dmriprep",
)
T1_to_EPI_AFF_KWARGS["from"] = "T1w"

NATIVE_TENSOR_KWARGS = dict(
    datatype="dwi",
    suffix="epiref",
    space="orig",
    compress=True,
    out_path_base="dmriprep",
)
COREG_TENSOR_KWARGS = dict(
    datatype="dwi",
    suffix="epiref",
    space="anat",
    compress=True,
    out_path_base="dmriprep",
)
