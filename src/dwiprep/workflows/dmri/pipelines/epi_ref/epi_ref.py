import nipype.pipeline.engine as pe
from dwiprep.workflows.dmri.pipelines.epi_ref.nodes import (
    INPUT_NODE,
    OUTPUT_NODE,
    DWIEXTRACT_NODE,
    MRMATH_NODE,
)
from dwiprep.workflows.dmri.pipelines.epi_ref.edges import (
    INPUT_TO_DWIEXTRACT_EDGES,
    DWIEXTRACT_TO_MRMATH_EDGES,
    MRMATH_TO_OUTPUT_EDGES,
)

EPI_REF = [
    (INPUT_NODE, DWIEXTRACT_NODE, INPUT_TO_DWIEXTRACT_EDGES),
    (DWIEXTRACT_NODE, MRMATH_NODE, DWIEXTRACT_TO_MRMATH_EDGES),
    (MRMATH_NODE, OUTPUT_NODE, MRMATH_TO_OUTPUT_EDGES),
]


def init_epi_ref_wf(name: str = "epi_reference_wf") -> pe.Workflow:
    """
    Initiate a workflow for generation of EPI referance image

    Parameters
    ----------
    name : str, optional
        Workflow's name, by default "epi_reference_wf"

    Returns
    -------
    pe.Workflow
        Initiated workflow
    """
    wf = pe.Workflow(name=name)
    wf.connect(EPI_REF)
    return wf
