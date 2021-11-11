import nipype.pipeline.engine as pe
from nipype.interfaces import utility as niu


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
    