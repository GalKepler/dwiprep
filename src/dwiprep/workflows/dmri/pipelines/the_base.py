import nipype.pipeline.engine as pe
import nipype.interfaces.mrtrix3 as mrt

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
    "bias_correct": {"use_ants": True},
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

OUTPUT_ENTITIES = {
    "denoise": {
        "out_file": {
            "output": False,
            "source": "dwi",
            "datatype": "dwi",
            "space": "dwi",
            "description": "denoised",
            "extension": "mif",
        },
        "noise": {
            "output": False,
            "source": "dwi",
            "datatype": "dwi",
            "space": "dwi",
            "description": "noise",
            "extension": "mif",
        },
    },
    "concatenate": {
        "out_file": {
            "output": False,
            "source": "fmap",
            "datatype": "fmap",
            "space": "dwi",
            "description": "phasediff",
            "extension": "mif",
            "suffix": "fmap",
        }
    },
    "preproc": {
        "out_file": {
            "output": False,
            "source": "dwi",
            "datatype": "dwi",
            "space": "dwi",
            "description": "eddynobiascorr",
            "extension": "mif",
        }
    },
    "bias_correct": {
        "out_file": {
            "output": True,
            "source": "dwi",
            "datatype": "dwi",
            "space": "dwi",
            "description": "preproc",
            "extension": "mif",
        }
    },
}


def build_pipeline(nodes: dict):
    workflow = pe.Workflow(name="dmriprep_wf")
    workflow.connect(
        [
            (
                nodes.get("datagrabber"),
                nodes.get("denoise"),
                [("dwi", "in_file")],
            ),
            (
                nodes.get("datagrabber"),
                nodes.get("concatenate"),
                [("fmap", "in_files")],
            ),
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
    "outputs": OUTPUT_ENTITIES,
    "generator": build_pipeline,
}
