"""
Nodes' configurations for *preprocessing* pipelines.
"""
import nipype.pipeline.engine as pe
from nipype.interfaces import utility as niu
from nipype.interfaces import mrtrix3 as mrt

from dwiprep.workflows.dmri.pipelines.tensor_estimation.configurations import (
    INPUT_NODE_FIELDS,
    OUTPUT_NODE_FIELDS,
    DWI2TENSOR_KWARGS,
    TENSOR2METRIC_KWARGS,
)

#: i/o
INPUT_NODE = pe.Node(
    niu.IdentityInterface(fields=INPUT_NODE_FIELDS),
    name="inputnode",
)
OUTPUT_NODE = pe.Node(
    niu.IdentityInterface(fields=OUTPUT_NODE_FIELDS),
    name="outputnode",
)

#: Building blocks
DWI2TENSOR_NODE = pe.Node(
    mrt.FitTensor(**DWI2TENSOR_KWARGS), name="fit_tensor"
)
TENSOR2METRIC = pe.Node(
    mrt.TensorMetrics(**TENSOR2METRIC_KWARGS), name="tensor2metric"
)
