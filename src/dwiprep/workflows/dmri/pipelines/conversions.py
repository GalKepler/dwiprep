import nipype.pipeline.engine as pe
from nipype.interfaces import utility as niu


def init_conversion_wf(name: str = "mif_eonversion_wf"):
    from nipype.interfaces import mrtrix3 as mrt

    wf = pe.Workflow(name=name)

    inputnode = pe.Node(
        niu.IdentityInterface(
            fields=[
                # DWI
                "dwi_file",
                "in_bvec",
                "in_bval",
                "dwi_json",
                # Fieldmaps
                "fmap_ap",
                "fmap_ap_json",
                "fmap_pa",
                "fmap_pa_json",
            ]
        ),
        name="inputnode",
    )
    outputnode = pe.Node(
        niu.IdentityInterface(
            fields=[
                "dwi_file",
                "fmap_ap",
                "fmap_pa",
            ]
        ),
        name="outputnode",
    )
    dwi_conversion = pe.Node(mrt.MRConvert(), name="dwi_conversion")
    fmap_ap_conversion = pe.Node(mrt.MRConvert(), name="fmap_ap_conversion")
    fmap_pa_conversion = pe.Node(mrt.MRConvert(), name="fmap_pa_conversion")

    wf.connect(
        [
            (
                inputnode,
                dwi_conversion,
                [
                    ("dwi_file", "in_file"),
                    ("dwi_json", "json_import"),
                    ("in_bvec", "in_bvec"),
                    ("in_bval", "in_bval"),
                ],
            ),
            (
                inputnode,
                fmap_ap_conversion,
                [
                    ("fmap_ap", "in_file"),
                    ("fmap_ap_json", "json_import"),
                ],
            ),
            (
                inputnode,
                fmap_pa_conversion,
                [
                    ("fmap_pa", "in_file"),
                    ("fmap_pa_json", "json_import"),
                ],
            ),
            (dwi_conversion, outputnode, [("out_file", "dwi_file")]),
            (fmap_ap_conversion, outputnode, [("out_file", "fmap_ap")]),
            (fmap_pa_conversion, outputnode, [("out_file", "fmap_pa")]),
        ]
    )
    return wf
