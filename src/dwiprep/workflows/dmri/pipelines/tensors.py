import nipype.pipeline.engine as pe
import nipype.interfaces.mrtrix3 as mrt

DEFAULT_KWARGS = {
    # dwi2tensor
    "fit_tensor": {},
    # tensor2metric
    "compute_metrics": {
        "out_fa": "FA.mif",
        "out_adc": "MD.mif",
        "out_ad": "AD.mif",
        "out_rd": "RD.mif",
        "out_cl": "CL.mif",
        "out_cs": "CS.mif",
        "out_evec": "EigenVector.mif",
        "out_eval": "EigenValue.mif",
    },
}
NODES = {
    # dwi2tensor
    "fit_tensor": pe.Node(mrt.FitTensor(), name="fit_tensor"),
    # compute_metrics
    "compute_metric": pe.Node(mrt.TensorMetrics(), name="compute_metrics"),
    # dwifslpreproc
}


### I'll write a function to append (?) the new workflow to the cleaning one.


def build_pipeline(nodes: dict):
    workflow = pe.Workflow(name="dmriprep")
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
    "generator": build_pipeline,
}
