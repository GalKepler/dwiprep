from nipype.pipeline import engine as pe
from nipype.interfaces import utility as niu
from nipype.interfaces import fsl


def init_apply_transform(
    in_fields: list, name="apply_transform_wf"
) -> pe.Workflow:
    """
    Initiates a workflow to apply pre-calculated (linear,rigid-body) transform to a list of files.

    Parameters
    ----------
    in_fields : list
        A list of string representing files to apply transform to.
    name : str, optional
        Workflow's name, by default "apply_transform_wf"

    Returns
    -------
    pe.Workflow
        Initiated workflow to apply pre-calculated transform on several files.
    """
    wf = pe.Workflow(name=name)
    metrics = in_fields.copy()
    in_fields += ["dwi_file", "epi_to_t1w_aff", "t1w_brain"]
    inputnode = pe.Node(
        niu.IdentityInterface(fields=in_fields), name="inputnode"
    )
    outputnode = pe.Node(
        niu.IdentityInterface(fields=in_fields), name="outputnode"
    )
    for field in metrics + ["dwi_file"]:
        node = pe.Node(
            fsl.ApplyXFM(apply_xfm=True), name=f"apply_transform_{field}"
        )
        wf.connect(
            [
                (
                    inputnode,
                    node,
                    [
                        ("epi_to_t1w_aff", "in_matrix_file"),
                        ("t1w_brain", "reference"),
                        (field, "in_file"),
                    ],
                ),
                (node, outputnode, [("out_file", field)]),
            ]
        )
    return wf
