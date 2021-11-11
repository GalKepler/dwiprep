import nipype.pipeline.engine as pe

from dwiprep.workflows.dmri.pipelines.preprocess.nodes import (
    INPUT_NODE,
    OUTPUT_NODE,
    DENOISE_NODE,
    INFER_PE_NODE,
    DWIPREPROC_NODE,
    BIASCORRECT_NODE,
)
from dwiprep.workflows.dmri.pipelines.preprocess.edges import (
    INPUT_TO_DENOISE_EDGES,
    INPUT_TO_DWIPREPROC_EDGES,
    DENOISE_TO_INFER_PE_EDGES,
    DENOISE_TO_DWIPREPROC_EDGES,
    INFER_PE_TO_DWIPREPROC_EDGES,
    DWIPREPROC_TO_BIASCORRECT_EDGES,
    BIASCORRECT_TO_OUTPUT_EDGES,
)


PREPROCESSING = [
    (INPUT_NODE, DENOISE_NODE, INPUT_TO_DENOISE_EDGES),
    (INPUT_NODE, DWIPREPROC_NODE, INPUT_TO_DWIPREPROC_EDGES),
    (DENOISE_NODE, INFER_PE_NODE, DENOISE_TO_INFER_PE_EDGES),
    (DENOISE_NODE, DWIPREPROC_NODE, DENOISE_TO_DWIPREPROC_EDGES),
    (INFER_PE_NODE, DWIPREPROC_NODE, INFER_PE_TO_DWIPREPROC_EDGES),
    (DWIPREPROC_NODE, BIASCORRECT_NODE, DWIPREPROC_TO_BIASCORRECT_EDGES),
    (BIASCORRECT_NODE, OUTPUT_NODE, BIASCORRECT_TO_OUTPUT_EDGES),
]


def init_preprocess_wf(name="preprocess_wf") -> pe.Workflow:
    """
    Initiates the preprocessing workflow.

    Parameters
    ----------
    name : str, optional
        Workflow's name, by default "preprocess_wf"

    Returns
    -------
    pe.Workflow
        Initiated workflow for preprocessing.
    """

    wf = pe.Workflow(name=name)
    wf.connect(PREPROCESSING)
    return wf
