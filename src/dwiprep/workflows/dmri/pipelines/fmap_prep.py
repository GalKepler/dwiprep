import nipype.pipeline.engine as pe
import nipype.interfaces.utility as niu
from nipype.interfaces import mrtrix3 as mrt


def init_phasediff_wf(name="phasediff_prep_wf"):
    wf = pe.Workflow(name=name)
    inputnode = pe.Node(
        niu.IdentityInterface(fields=["fmap_ap", "fmap_pa"]),
        name="inputnode",
    )
    merge_node = pe.Node(niu.Merge(numinputs=2), name="merge_files")
    mrcat_node = pe.Node(mrt.MRCat(axis=3), name="mrcat")
    outputnode = pe.Node(
        niu.IdentityInterface(fields=["merged_phasediff"]), name="outputnode"
    )
    wf.connect(
        [
            (inputnode, merge_node, [("fmap_ap", "in1"), ("fmap_pa", "in2")]),
            (merge_node, mrcat_node, [("out", "in_files")]),
            (mrcat_node, outputnode, [("out_file", "merged_phasediff")]),
        ]
    )
    return wf


def add_fieldmaps_to_wf(
    inputnode: pe.Node,
    conversion_wf: pe.Workflow,
    epi_ref_wf: pe.Workflow,
    phasediff_wf: pe.Workflow,
):
    fmap_ap, fmap_pa = [
        getattr(inputnode.inputs, key, None) for key in ["fmap_ap", "fmap_pa"]
    ]
    if fmap_ap and fmap_pa:
        connection = [
            (
                conversion_wf,
                phasediff_wf,
                [
                    ("outputnode.fmap_ap", "inputnode.fmap_ap"),
                    ("outputnode.fmap_pa", "inputnode.fmap_pa"),
                ],
            )
        ]

    else:
        if fmap_pa is not None:
            connection = [
                (
                    epi_ref_wf,
                    phasediff_wf,
                    [
                        ("outputnode.epi_ref_file", "inputnode.fmap_ap"),
                    ],
                ),
                (
                    conversion_wf,
                    phasediff_wf,
                    [("outputnode.fmap_pa", "inputnode.fmap_pa")],
                ),
            ]

        elif fmap_ap is not None:
            connection = [
                (
                    epi_ref_wf,
                    phasediff_wf,
                    [
                        ("outputnode.epi_ref_file", "inputnode.fmap_pa"),
                    ],
                ),
                (
                    conversion_wf,
                    phasediff_wf,
                    [("outputnode.fmap_ap", "inputnode.fmap_ap")],
                ),
            ]
        else:
            raise NotImplementedError(
                "Currently fieldmap-based SDC is mandatory and thus requires at least one opposite single-volume EPI image."
            )
    return connection
