import nipype.pipeline.engine as pe
from nipype.interfaces import mrtrix3 as mrt
import nipype.interfaces.utility as niu


def init_epi_ref_wf(name: str = "epi_reference_wf") -> pe.Workflow:
    """
    Build a workflow for generation of EPI referance image

    Parameters
    ----------
    inputnode : pe.Node
        Pipeline's input node

    Returns
    -------
    Workflow
        EPI-reference generation workflow
    """
    wf = pe.Workflow(name=name)
    inputnode = pe.Node(
        niu.IdentityInterface(fields=["dwi_file"]), name="inputnode"
    )
    outputnode = pe.Node(
        niu.IdentityInterface(fields=["epi_ref_file"]), name="outputnode"
    )
    dwiextract = pe.Node(
        mrt.DWIExtract(bzero=True, out_file="b0.mif"), name="dwiextract"
    )
    mrmath = pe.Node(
        mrt.MRMath(operation="mean", axis=3, out_file="mean_b0.mif"),
        name="mrmath",
    )
    wf.connect(
        [
            (inputnode, dwiextract, [("dwi_file", "in_file")]),
            (
                dwiextract,
                mrmath,
                [
                    ("out_file", "in_file"),
                ],
            ),
            (mrmath, outputnode, [("out_file", "epi_ref_file")]),
        ]
    )
    return wf
