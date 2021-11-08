import nipype.pipeline.engine as pe
from nipype.interfaces import mrtrix3 as mrt
import nipype.interfaces.utility as niu


def init_tensor_wf(name="tensor_estimation_wf"):
    wf = pe.Workflow(name=name)
    inputnode = pe.Node(
        niu.IdentityInterface(fields=["dwi_file"]), name="inputnode"
    )
    out_fields = ["fa", "adc", "ad", "rd", "cl", "cp", "cs", "evec", "eval"]
    outputnode = pe.Node(
        niu.IdentityInterface(fields=out_fields),
        name="outputnode",
    )
    dwi2tensor = pe.Node(mrt.FitTensor(), name="fit_tensor")
    kwargs = {f"out_{metric}": f"{metric}.nii.gz" for metric in out_fields}
    tensor2metric = pe.Node(mrt.TensorMetrics(**kwargs), name="tensor2metric")
    wf.connect(
        [
            (inputnode, dwi2tensor, [("dwi_file", "in_file")]),
            (dwi2tensor, tensor2metric, [("out_file", "in_file")]),
        ]
    )

    for key, value in kwargs.items():
        wf.connect([(tensor2metric, outputnode, [(key, value.split(".")[0])])])
    return wf, out_fields
