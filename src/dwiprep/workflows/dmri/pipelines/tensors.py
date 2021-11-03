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
    "compute_metrics": pe.Node(mrt.TensorMetrics(), name="compute_metrics"),
    # dwifslpreproc
}


### I'll write a function to append (?) the new workflow to the cleaning one.


def build_pipeline(nodes: dict):
    workflow = pe.Workflow(name="dmriprep")
    workflow.connect(
        [
            (
                nodes.get("fit_tensor"),
                nodes.get("compute_metrics"),
                [("out_file", "in_file")],
            ),
        ]
    )
    return workflow


TENSOR_FIT = {
    "nodes": NODES,
    "kwargs": DEFAULT_KWARGS,
    "generator": build_pipeline,
}
