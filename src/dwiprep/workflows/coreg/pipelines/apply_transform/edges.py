"""
Edges' configurations for *apply_transforms* pipelines.
"""
INPUT_TO_TENSOR_XFM_EDGES = [
    ("tensor_metrics", "in_file"),
    ("epi_to_t1w_aff", "in_matrix_file"),
    ("t1w_brain", "reference"),
]
INPUT_TO_DWI_XFM_EDGES = [
    ("dwi_file", "in_file"),
    ("epi_to_t1w_aff", "in_matrix_file"),
    ("t1w_brain", "reference"),
]

TENSOR_XFM_TO_OUTPUT_EDGES = [("out_file", "tensor_metrics")]
DWI_XFM_TO_OUTPUT_EDGES = [("out_file", "dwi_file")]
