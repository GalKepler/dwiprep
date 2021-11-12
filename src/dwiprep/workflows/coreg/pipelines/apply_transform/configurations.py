"""
Configurations for *apply_transform* pipelines
"""

INPUT_NODE_FIELDS = [
    "tensor_metrics",
    "dwi_file",
    "epi_to_t1w_aff",
    "t1w_brain",
]
OUTPUT_NODE_FIELDS = ["tensor_metrics", "dwi_file"]

APPLY_XFM_KWARGS = dict(apply_xfm=True)
