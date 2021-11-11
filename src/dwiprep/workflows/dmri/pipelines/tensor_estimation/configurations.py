"""
Configurations for *preprocessing* pipeline.
"""
#: i/o
INPUT_NODE_FIELDS = ["dwi_file"]
OUTPUT_NODE_FIELDS = [
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

#: Keyword arguments
DWI2TENSOR_KWARGS = dict()
TENSOR2METRIC_KWARGS = {
    f"out_{metric}": f"{metric}.nii.gz" for metric in OUTPUT_NODE_FIELDS
}
