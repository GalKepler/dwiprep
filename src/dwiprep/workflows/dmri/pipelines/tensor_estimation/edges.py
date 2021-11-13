"""
Connections configurations for *preprocessing* pipelines.
"""
from dwiprep.workflows.dmri.pipelines.tensor_estimation.configurations import (
    TENSOR2METRIC_KWARGS,
)

#: i/o
INPUT_TO_DWI2TENSOR_EDGES = [("dwi_file", "in_file")]
DWI2TENSOR_TO_TENSOR2METRIC_EDGES = [("out_file", "in_file")]
TENSOR2METRIC_TO_LISTIFY_EDGES = []
#: all metrics measured
for input_num, key in enumerate(TENSOR2METRIC_KWARGS):
    TENSOR2METRIC_TO_LISTIFY_EDGES.append((key, f"in{input_num+1}"))
LISTIFY_TO_OUTPUT_EDGES = [("out", "metrics")]
