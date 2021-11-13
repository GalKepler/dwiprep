import nipype.pipeline.engine as pe
from nipype.interfaces import mrtrix3 as mrt
import nipype.interfaces.utility as niu
from dwiprep.workflows.dmri.pipelines.tensor_estimation.configurations import (
    OUTPUT_NODE_FIELDS,
)
from dwiprep.workflows.dmri.pipelines.tensor_estimation.nodes import (
    INPUT_NODE,
    OUTPUT_NODE,
    DWI2TENSOR_NODE,
    TENSOR2METRIC_NODE,
    LISTIFY_NODE,
)
from dwiprep.workflows.dmri.pipelines.tensor_estimation.edges import (
    INPUT_TO_DWI2TENSOR_EDGES,
    DWI2TENSOR_TO_TENSOR2METRIC_EDGES,
    TENSOR2METRIC_TO_LISTIFY_EDGES,
    LISTIFY_TO_OUTPUT_EDGES,
)

TENSOR_ESTIMATION = [
    (INPUT_NODE, DWI2TENSOR_NODE, INPUT_TO_DWI2TENSOR_EDGES),
    (DWI2TENSOR_NODE, TENSOR2METRIC_NODE, DWI2TENSOR_TO_TENSOR2METRIC_EDGES),
    (TENSOR2METRIC_NODE, LISTIFY_NODE, TENSOR2METRIC_TO_LISTIFY_EDGES),
    (LISTIFY_NODE, OUTPUT_NODE, LISTIFY_TO_OUTPUT_EDGES),
]


def init_tensor_wf(name="tensor_estimation_wf") -> pe.Workflow:
    """
    Initiates a tensor estimation workflow

    Parameters
    ----------
    name : str, optional
        Workflow's name, by default "tensor_estimation_wf"

    Returns
    -------
    pe.Workflow
        Initiated workflow for tensor and tensor-derived metrics estimation.
    """

    wf = pe.Workflow(name=name)
    wf.connect(TENSOR_ESTIMATION)
    return wf
