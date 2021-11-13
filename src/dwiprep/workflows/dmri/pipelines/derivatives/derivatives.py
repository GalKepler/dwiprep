import nipype.pipeline.engine as pe
from nipype.interfaces import utility as niu
from dwiprep.workflows.dmri.pipelines.derivatives.nodes import (
    INPUT_NODE,
    PHASEDIFF_LIST_NODE,
    PHASEDIFF_DDS_NODE,
    NATIVE_DWI_LIST_NODE,
    NATIVE_DWI_DDS_NODE,
    COREG_DWI_DDS_NODE,
    NATIVE_SBREF_LIST_NODE,
    NATIVE_SBREF_DDS_NODE,
    COREG_SBREF_DDS_NODE,
    EPI_TO_T1_NODE,
    T1_TO_EPI_NODE,
    NATIVE_TENSOR_WF,
    COREG_TENSOR_WF,
)
from dwiprep.workflows.dmri.pipelines.derivatives.edges import (
    INPUT_TO_PHASEDIFF_LIST_EDGES,
    INPUT_TO_PHASEDIFF_DDS_EDGES,
    PHASEDIFF_LIST_TO_DDS_EDGES,
    INPUT_TO_NATIVE_DWI_LIST_EDGES,
    INPUT_TO_NATIVE_DWI_DDS_EDGES,
    NATIVE_DWI_LIST_TO_DDS_EDGES,
    INPUT_TO_COREG_DWI_DDS_EDGES,
    INPUT_TO_NATIVE_SBREF_LIST_EDGES,
    INPUT_TO_NATIVE_SBREF_DDS_EDGES,
    NATIVE_SBREF_LIST_TO_DDS_EDGES,
    INPUT_TO_COREG_SBREF_DDS_EDGES,
    INPUT_TO_EPI_TO_T1_EDGES,
    INPUT_TO_T1_TO_EPI_EDGES,
    INPUT_TO_NATIVE_TENSOR_EDGES,
    INPUT_TO_COREG_TENSOR_EDGES,
)

DERIVATIVES_DS = [
    #: Phasediff
    (INPUT_NODE, PHASEDIFF_LIST_NODE, INPUT_TO_PHASEDIFF_LIST_EDGES),
    (INPUT_NODE, PHASEDIFF_DDS_NODE, INPUT_TO_PHASEDIFF_DDS_EDGES),
    (PHASEDIFF_LIST_NODE, PHASEDIFF_DDS_NODE, PHASEDIFF_LIST_TO_DDS_EDGES),
    #: Native DWI
    (INPUT_NODE, NATIVE_DWI_LIST_NODE, INPUT_TO_NATIVE_DWI_LIST_EDGES),
    (INPUT_NODE, NATIVE_DWI_DDS_NODE, INPUT_TO_NATIVE_DWI_DDS_EDGES),
    (NATIVE_DWI_LIST_NODE, NATIVE_DWI_DDS_NODE, NATIVE_DWI_LIST_TO_DDS_EDGES),
    #: Coreg DWI
    (INPUT_NODE, COREG_DWI_DDS_NODE, INPUT_TO_COREG_DWI_DDS_EDGES),
    #: Native EPI reference
    (INPUT_NODE, NATIVE_SBREF_LIST_NODE, INPUT_TO_NATIVE_SBREF_LIST_EDGES),
    (INPUT_NODE, NATIVE_SBREF_DDS_NODE, INPUT_TO_NATIVE_SBREF_DDS_EDGES),
    (
        NATIVE_SBREF_LIST_NODE,
        NATIVE_SBREF_DDS_NODE,
        NATIVE_SBREF_LIST_TO_DDS_EDGES,
    ),
    #: Coreg EPI reference
    (INPUT_NODE, COREG_SBREF_DDS_NODE, INPUT_TO_COREG_SBREF_DDS_EDGES),
    #: Transformations
    (INPUT_NODE, EPI_TO_T1_NODE, INPUT_TO_EPI_TO_T1_EDGES),
    (INPUT_NODE, T1_TO_EPI_NODE, INPUT_TO_T1_TO_EPI_EDGES),
    #: Native tensor-derived metrics
    (INPUT_NODE, NATIVE_TENSOR_WF, INPUT_TO_NATIVE_TENSOR_EDGES),
    #: Coreg tensor-derived metrics
    (INPUT_NODE, COREG_TENSOR_WF, INPUT_TO_COREG_TENSOR_EDGES),
]


def init_derivatives_wf(name="dmri_derivatives_wf") -> pe.Workflow:
    """
    Initiates a workflow comprised of a battery of DerivativesDataSinks to store output files in their correct locations.

    Parameters
    ----------
    name : str, optional
        Workflow's name, by default "dmri_derivatives_wf"

    Returns
    -------
    pe.Workflow
        An initiated workflow for storing output files in their correct locations.
    """
    wf = pe.Workflow(name=name)
    wf.connect(DERIVATIVES_DS)
    return wf
