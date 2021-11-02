from nipype.interfaces.mrtrix3.preprocess import DWIBiasCorrect, DWIDenoise
from nipype.interfaces.mrtrix3.utils import MRMath
import nipype.pipeline.engine as pe
from nipype import Node
import nipype.interfaces.mrtrix3 as mrt
from nipype.interfaces.utility import Merge
from dwiprep.workflows.dmri.utils.utils import return_files_as_list


def init_mrconvert_node(data_type: str, kwargs: dict) -> pe.Node:
    """
    Instanciates a *MRConvert*-based node with predefined kwargs

    Parameters
    ----------
    data_type : str
        Data type to be converted
    kwargs : dict
        Keyword arguments for MRConvert

    Returns
    -------
    pe.Node
        A pe.Node instance with predefined kwargs.
    """
    return pe.Node(mrt.MRConvert(**kwargs), name=f"{data_type}_mif_conversion")


DWIEXTRACT_KWARGS = {"bzero": True}
MRMATH_KWARGS = {"operation": "mean", "axis": 3}
MRCAT_KWARGS = {"axis": 3}
DWIDENOISE_KWARGS = {}
DWIFSLPREPROC_KWARGS = {
    "rpe_options": "pair",
    "align_seepi": True,
    "eddy_options": " --slm=linear",
}
DWIBIASCORRECT_KWARGS = {"use_ants": True}
DWI2TENSOR_KWARGS = {}
# tensor2metric

TENSOR2METRICS_KWARGS = {
    "out_fa": "FA.mif",
    "out_adc": "MD.mif",
    "out_ad": "AD.mif",
    "out_rd": "RD.mif",
    "out_cl": "CL.mif",
    "out_cs": "CS.mif",
    "out_evec": "EigenVector.mif",
    "out_eval": "EigenValue.mif",
}


def init_preprocess_wf(
    dwiextract_kwargs: dict = DWIEXTRACT_KWARGS,
    mrmath_kwargs: dict = MRMATH_KWARGS,
    mrcat_kwargs: dict = MRCAT_KWARGS,
    dwidenoise_kwargs: dict = DWIDENOISE_KWARGS,
    dwifslpreproc_kwargs: dict = DWIFSLPREPROC_KWARGS,
    dwibiascorrect_kwargs: dict = DWIBIASCORRECT_KWARGS,
):

    wf = pe.Workflow(name="preprocess")
    dwiextract = pe.Node(
        mrt.DWIExtract(**dwiextract_kwargs), name="dwiextract"
    )
    mrmath = pe.Node(mrt.MRMath(**mrmath_kwargs), name="mrmath")
    list_files = pe.Node(Merge(numinputs=2), name="list_files")
    mrcat = pe.Node(mrt.MRCat(**mrcat_kwargs), name="mrcat")
    dwidenoise = pe.Node(
        mrt.DWIDenoise(**dwidenoise_kwargs), name="dwidenoise"
    )
    dwifslpreproc = pe.Node(
        mrt.DWIPreproc(**dwifslpreproc_kwargs), name="dwifslpreproc"
    )
    biascorrect = pe.Node(
        mrt.DWIBiasCorrect(**dwibiascorrect_kwargs), name="biascorrect"
    )
    wf.connect(
        [
            (dwiextract, mrmath, [("out_file", "in_file")]),
            (mrmath, list_files, [("out_file", "in1")]),
            (list_files, mrcat, [("out", "in_files")]),
            (mrcat, dwifslpreproc, [("out_file", "in_epi")]),
            (dwidenoise, dwifslpreproc, [("out_file", "in_file")]),
            (dwifslpreproc, biascorrect, [("out_file", "in_file")]),
        ]
    )
    return wf


def connect_conversion_to_wf(mif_data: dict, preproc_wf: pe.Workflow):
    wf = pe.Workflow(name="cleaning")
    dwi_node = mif_data.get("dwi")
    fmap_node = mif_data.get("fmap")
    wf.connect(
        [
            (dwi_node, preproc_wf, [("out_file", "dwiextract.in_file")]),
            (dwi_node, preproc_wf, [("out_file", "dwidenoise.in_file")]),
            (fmap_node, preproc_wf, [("out_file", "list_files.in2")]),
        ]
    )
    return wf


def connect_tensor_wf(
    preproc_wf: pe.Workflow,
    dwi2tensor_kwargs: dict = DWI2TENSOR_KWARGS,
    tensor2metrics_kwargs: dict = TENSOR2METRICS_KWARGS,
):
    dwi2tensor = Node(mrt.FitTensor(**dwi2tensor_kwargs), name="fit_tensor")
    tensor2metrics = Node(
        mrt.TensorMetrics(**tensor2metrics_kwargs), name="compute_metrics"
    )

    wf = pe.Workflow(name="tensor_estimation")
    wf.connect(
        [
            (
                preproc_wf,
                dwi2tensor,
                [("preprocess.biascorrect.out_file", "in_file")],
            ),
            (dwi2tensor, tensor2metrics, [("out_file", "in_file")]),
        ],
    )
    return wf
