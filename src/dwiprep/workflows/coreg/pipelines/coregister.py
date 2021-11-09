from nipype.pipeline import engine as pe
from nipype.interfaces import utility as niu
from nipype.interfaces import fsl, ants
from nipype.pipeline.engine import workflows


def init_epireg_wf(
    name="epi_reg_wf",
):
    wf = pe.Workflow(name=name)
    #     workflow.__desc__ = """\
    # The EPI reference was then co-registered to the T1w reference using
    # `bbregister` (FreeSurfer) which implements boundary-based registration [@bbr].
    # Co-registration was configured with {dof} degrees of freedom{reason}.
    # """.format(
    #         dof={6: "six", 9: "nine", 12: "twelve"}[epi2t1w_dof],
    #         reason=""
    #         if epi2t1w_dof == 6
    #         else "to account for distortions remaining in the EPI reference",
    #     )

    inputnode = pe.Node(
        niu.IdentityInterface(["in_file", "t1w_brain", "t1w_head"]),
        name="inputnode",
    )
    outputnode = pe.Node(
        niu.IdentityInterface(
            ["epi_to_t1w_aff", "t1w_to_epi_aff", "epi_to_t1w"]
        ),
        name="outputnode",
    )
    epi_reg = pe.Node(fsl.EpiReg(), name="epi_reg")
    inv_transform = pe.Node(fsl.ConvertXFM(invert_xfm=True), name="invert_xfm")

    wf.connect(
        [
            (
                inputnode,
                epi_reg,
                [
                    ("t1w_brain", "t1_brain"),
                    ("t1w_head", "t1_head"),
                    ("in_file", "epi"),
                ],
            ),
            (epi_reg, inv_transform, [("epi2str_mat", "in_file")]),
            (
                epi_reg,
                outputnode,
                [
                    ("epi2str_mat", "epi_to_t1w_aff"),
                    ("out_file", "epi_to_t1w"),
                ],
            ),
            (
                inv_transform,
                outputnode,
                [
                    ("out_file", "t1w_to_epi_aff"),
                ],
            ),
        ]
    )
    return wf


def init_apply_transform(in_fields: list, name="apply_transform_wf"):
    wf = pe.Workflow(name=name)
    in_fields += ["dwi_file", "epi_to_t1w_aff", "t1w_brain"]
    inputnode = pe.Node(
        niu.IdentityInterface(in_fields=in_fields), name="inputnode"
    )
    outputnode = pe.Node(
        niu.IdentityInterface(in_fields=in_fields), name="outputnode"
    )
    for field in in_fields:
        node = pe.Node(ants.ApplyTransforms(), name=f"apply_transform_{field}")
        wf.connect(
            [
                (
                    inputnode,
                    node,
                    [
                        ("epi_to_t1w_aff", "transforms"),
                        ("t1w_brain", "reference_image"),
                        (field, "input_image"),
                    ],
                )
            ]
        )
