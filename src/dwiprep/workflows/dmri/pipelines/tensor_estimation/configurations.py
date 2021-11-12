"""
Configurations for *preprocessing* pipeline.
"""

METRICS = [
    "fa",
    "adc",
    "ad",
    "rd",
    "cl",
    "cp",
    "cs",
    "evec",
    "eval",
]
#: i/o
INPUT_NODE_FIELDS = ["dwi_file"]
OUTPUT_NODE_FIELDS = ["metrics"]

#: Keyword arguments
DWI2TENSOR_KWARGS = dict()
TENSOR2METRIC_KWARGS = {
    f"out_{metric}": f"{metric}.nii.gz" for metric in METRICS
}
LISTIFY_KWARGS = dict(numinputs=len(METRICS))
