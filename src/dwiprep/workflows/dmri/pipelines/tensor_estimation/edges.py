"""
Connections configurations for *preprocessing* pipelines.
"""
from dwiprep.workflows.dmri.pipelines.tensor_estimation.configurations import (
    TENSOR2METRIC_KWARGS,
)

#: i/o
INPUT_TO_DWI2TENSOR_EDGES = [("dwi_file", "in_file")]
DWI2TENSOR_TO_TENSOR2METRIC_EDGES = [("out_file", "in_file")]

#: all metrics measured
TENSOR2METRIC_TO_OUTPUT_EDGES = []
for key in TENSOR2METRIC_KWARGS:
    TENSOR2METRIC_TO_OUTPUT_EDGES.append((key, key.split("_")[-1]))
