import nipype.pipeline.engine as pe
import nipype.interfaces.mrtrix3 as mrt
from nipype.pipeline.engine.nodes import Node

DEFAULT_KWARGS = {
    # dwidenoise
    "denoise": {},
    # mrcat
    "concatenate": {},
    # dwifslpreproc
    "preproc": {
        "rpe_options": "pair",
        "align_seepi": True,
        "eddy_options": " --slm=linear",
    },
    # dwibiascorrect
    "bias_correct": {},
}
NODES = {
    # dwidenoise
    "denoise": pe.Node(mrt.DWIDenoise(), name="denoise"),
    # mrcat
    "concatenate": pe.Node(mrt.MRCat(), name="mrcat"),
    # dwifslpreproc
    "preproc": pe.Node(
        mrt.DWIPreproc(),
        name="dwifslpreproc",
    ),
    # dwibiascorrect
    "bias_correct": pe.Node(mrt.DWIBiasCorrect(), name="dwibiascorrect"),
}


def build_pipeline(nodes: dict):
    workflow = pe.Workflow(name="TheBaseDWIPrep")
    workflow.connect(
        [
            (
                nodes.get("denoise"),
                nodes.get("preproc"),
                [("out_file", "in_file")],
            ),
            (
                nodes.get("concatenate"),
                nodes.get("preproc"),
                [("out_file", "in_epi")],
            ),
            (
                nodes.get("preproc"),
                nodes.get("bias_correct"),
                [("out_file", "in_file")],
            ),
        ]
    )
    return workflow


THE_BASE = {
    "nodes": NODES,
    "kwargs": DEFAULT_KWARGS,
    "generator": build_pipeline,
}
