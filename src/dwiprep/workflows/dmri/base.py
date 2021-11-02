from bids.layout.layout import BIDSLayout
from nipype.interfaces.mrtrix3.preprocess import DWIBiasCorrect, DWIDenoise
from nipype.interfaces.mrtrix3.utils import MRCat, MRMath
import nipype.pipeline.engine as pe
from nipype import Node, Function, interfaces
import nipype.interfaces.io as nio
import nipype.interfaces.mrtrix3 as mrt
from nipype.interfaces.utility import Merge
from dwiprep.workflows.dmri.utils.utils import (
    infer_phase_encoding_direction_mif,
)
from dwiprep.interfaces.mrconvert import map_list_to_kwargs, parse_dict_by_keys
from nipype.interfaces.io import DataSink
from pathlib import Path

DWIEXTRACT_KWARGS = {
    "inputs": {"bzero": True, "out_file": "b0.mif"},
    "outputs": {
        "out_file": {"description": "b0", "space": "dwi", "extension": "mif"}
    },
}
MRMATH_KWARGS = {
    "inputs": {"operation": "mean", "axis": 3, "out_file": "mean_b0.mif"},
    "outputs": {
        "out_file": {
            "description": "meanb0",
            "space": "dwi",
            "extension": "mif",
        }
    },
}
MRCAT_KWARGS = {
    "inputs": {"axis": 3},
    "outputs": {
        "out_file": {
            "direction": None,
            "description": "phasediff",
            "space": "dwi",
            "datatype": "fmap",
            "extension": "mif",
        }
    },
}
DWIDENOISE_KWARGS = {
    "inputs": {},
    "outputs": {
        "out_file": {
            "description": "denoised",
            "space": "dwi",
            "extension": "mif",
        },
        "noise": {"description": "noise", "space": "dwi", "extension": "mif"},
    },
}
DWIFSLPREPROC_KWARGS = {
    "inputs": {
        "rpe_options": "pair",
        "align_seepi": True,
        "eddy_options": " --slm=linear",
    },
    "outputs": {
        "out_file": {
            "description": "SDCorrected",
            "space": "dwi",
            "extension": "mif",
        }
    },
}
DWIBIASCORRECT_KWARGS = {
    "inputs": {"use_ants": True},
    "outputs": {
        "out_file": {
            "description": "biascorr",
            "space": "dwi",
            "extension": "mif",
        }
    },
}
DWI2TENSOR_KWARGS = {
    "inputs": {},
    "outputs": {
        "out_file": {
            "description": "tensor",
            "space": "dwi",
            "datatype": "tensor",
            "extension": "mif",
        }
    },
}
# tensor2metric

TENSOR2METRICS_KWARGS = {
    "inputs": {},
    "outputs": {
        "out_fa": {
            "description": "FA",
            "space": "dwi",
            "datatype": "tensor",
            "extension": "mif",
        },
        "out_adc": {
            "description": "MD",
            "space": "dwi",
            "datatype": "tensor",
            "extension": "mif",
        },
        "out_ad": {
            "description": "AD",
            "space": "dwi",
            "datatype": "tensor",
            "extension": "mif",
        },
        "out_rd": {
            "description": "RD",
            "space": "dwi",
            "datatype": "tensor",
            "extension": "mif",
        },
        "out_cl": {
            "description": "CL",
            "space": "dwi",
            "datatype": "tensor",
            "extension": "mif",
        },
        "out_cs": {
            "description": "CS",
            "space": "dwi",
            "datatype": "tensor",
            "extension": "mif",
        },
        "out_cp": {
            "description": "CP",
            "space": "dwi",
            "datatype": "tensor",
            "extension": "mif",
        },
        "out_evec": {
            "description": "EigenVector",
            "space": "dwi",
            "datatype": "tensor",
            "extension": "mif",
        },
        "out_eval": {
            "description": "EigenValue",
            "space": "dwi",
            "datatype": "tensor",
            "extension": "mif",
        },
    },
}


def init_datagrabber(
    bids_dir: str,
    participant_label: str,
    queries: dict,
    session: str = None,
):
    grabber = nio.BIDSDataGrabber(base_dir=bids_dir)
    grabber.inputs.subject = participant_label
    grabber.inputs.output_query = queries
    name = f"sub-{participant_label}"
    if session:
        grabber.inputs.session = session
        name = f"{name}_ses-{session}"
    return pe.Node(grabber, name=f"{name}_grabber")


def get_conversion_connector(data_type: str):
    connector = [("in_file", "in_file"), ("json_import", "json_import")]
    if data_type in ["dwi"]:
        connector += [("in_bvec", "in_bvec"), ("in_bval", "in_bval")]
    return connector


def init_mrconvert_wf(
    data_type: str, datagrabber: pe.Node, mapping: dict
) -> pe.Node:
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
    mapping_node = pe.Node(
        Function(
            input_names=["file_names", "mapping"],
            output_names=["out_dict"],
            function=map_list_to_kwargs,
        ),
        name="map_files",
    )
    mapping_node.inputs.mapping = mapping
    kwarg_node = pe.Node(
        Function(
            input_names=["kwargs"],
            output_names=["in_file", "json_import", "in_bvec", "in_bval"],
            function=parse_dict_by_keys,
        ),
        name="parse_dict",
    )
    conversion = pe.Node(mrt.MRConvert(), name=f"mif_conversion")
    wf = pe.Workflow(name=f"{data_type}_conversion")
    wf.connect(
        [
            (datagrabber, mapping_node, [(data_type, "file_names")]),
            (mapping_node, kwarg_node, [("out_dict", "kwargs")]),
            (kwarg_node, conversion, get_conversion_connector(data_type)),
        ]
    )
    return wf


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


def build_output_path(
    bids_dir: str, destination: str, source: str, entities: dict = {}
):
    OUTPUT_PATTERNS = "sub-{subject}/[ses-{session}/][{datatype}/]sub-{subject}[_ses-{session}][_acq-{acquisition}][_dir-{direction}][_space-{space}][_desc-{description}]_{suffix}.{extension}"
    from bids import BIDSLayout
    from pathlib import Path

    layout = BIDSLayout(bids_dir)
    base_entities = layout.parse_file_entities(source)
    target_entities = base_entities.copy()
    for key, val in entities.items():
        entities[key] = val
    output = str(
        Path(destination)
        / layout.build_path(
            target_entities,
            path_patterns=OUTPUT_PATTERNS,
            validate=False,
            absolute_paths=False,
        )
    )
    return output


def make_node(bids_dir, destination, source, interface, kwargs, name):
    interface = interface(**kwargs.get("inputs"))
    node = pe.Node(interface, name=name)
    for key, val in kwargs.get("outputs").items():
        target = build_output_path(bids_dir, destination, source, val)
        node.set_input(key, target)
    return node


def init_preprocess_wf(
    bids_dir: str,
    destination: str,
    dwi: str,
    fmap: str,
    dwiextract_kwargs: dict = DWIEXTRACT_KWARGS,
    mrmath_kwargs: dict = MRMATH_KWARGS,
    mrcat_kwargs: dict = MRCAT_KWARGS,
    dwidenoise_kwargs: dict = DWIDENOISE_KWARGS,
    dwifslpreproc_kwargs: dict = DWIFSLPREPROC_KWARGS,
    dwibiascorrect_kwargs: dict = DWIBIASCORRECT_KWARGS,
):
    wf = pe.Workflow(name="preprocess")
    dwiextract = make_node(
        bids_dir,
        destination,
        dwi,
        mrt.DWIExtract,
        dwiextract_kwargs,
        "dwiextract",
    )
    # dwiextract = pe.Node(
    #     mrt.DWIExtract(**dwiextract_kwargs), name="dwiextract"
    # )
    mrmath = make_node(
        bids_dir,
        destination,
        dwi,
        mrt.MRMath,
        mrmath_kwargs,
        "mrmath",
    )
    # mrmath = pe.Node(mrt.MRMath(**mrmath_kwargs), name="mrmath")
    list_files = pe.Node(Merge(numinputs=2), name="list_files")
    mrcat = make_node(
        bids_dir,
        destination,
        fmap,
        mrt.MRCat,
        mrcat_kwargs,
        "mrcat",
    )
    # mrcat = pe.Node(mrt.MRCat(**mrcat_kwargs), name="mrcat")
    dwidenoise = make_node(
        bids_dir,
        destination,
        dwi,
        mrt.DWIDenoise,
        dwidenoise_kwargs,
        "dwidenoise",
    )
    # dwidenoise = pe.Node(
    #     mrt.DWIDenoise(**dwidenoise_kwargs), name="dwidenoise"
    # )
    infer_pe = pe.Node(
        Function(
            input_names=["in_file"],
            output_names=["pe_dir"],
            function=infer_phase_encoding_direction_mif,
        ),
        name="infer_pe",
    )
    dwifslpreproc = make_node(
        bids_dir,
        destination,
        dwi,
        mrt.DWIPreproc,
        dwifslpreproc_kwargs,
        "dwifslpreproc",
    )
    # dwifslpreproc = pe.Node(
    #     mrt.DWIPreproc(**dwifslpreproc_kwargs), name="dwifslpreproc"
    # )
    biascorrect = make_node(
        bids_dir,
        destination,
        dwi,
        mrt.DWIBiasCorrect,
        dwibiascorrect_kwargs,
        "biascorrect",
    )
    # biascorrect = pe.Node(
    #     mrt.DWIBiasCorrect(**dwibiascorrect_kwargs), name="biascorrect"
    # )
    wf.connect(
        [
            (dwiextract, mrmath, [("out_file", "in_file")]),
            # (dwiextract, sinker_node, [("out_file", "dwi_b0s")]),
            # (mrmath, sinker_node, [("out_file", "mean_b0")]),
            (mrmath, list_files, [("out_file", "in1")]),
            (list_files, mrcat, [("out", "in_files")]),
            # (mrcat, sinker_node, [("out_file", "phasediff")]),
            (mrcat, dwifslpreproc, [("out_file", "in_epi")]),
            (dwidenoise, dwifslpreproc, [("out_file", "in_file")]),
            (dwidenoise, infer_pe, [("out_file", "in_file")]),
            (infer_pe, dwifslpreproc, [("pe_dir", "pe_dir")]),
            # (dwidenoise, sinker_node, [("out_file", "denoised")]),
            # (dwifslpreproc, sinker_node, [("out_file", "SDC")]),
            (dwifslpreproc, biascorrect, [("out_file", "in_file")]),
            # (biascorrect, sinker_node, [("out_file", "biascorr")]),
        ]
    )
    return wf


def connect_conversion_to_wf(
    conversion_wfs: dict, preproc_wf: pe.Workflow, sinker: Node
):
    wf = pe.Workflow(name="cleaning")
    dwi_wf = conversion_wfs.get("dwi")
    fmap_wf = conversion_wfs.get("fmap")
    wf.connect(
        [
            (
                dwi_wf,
                preproc_wf,
                [("mif_conversion.out_file", "dwiextract.in_file")],
            ),
            (dwi_wf, sinker, [("mif_conversion.out_file", "DWI")]),
            (
                dwi_wf,
                preproc_wf,
                [("mif_conversion.out_file", "dwidenoise.in_file")],
            ),
            (
                fmap_wf,
                preproc_wf,
                [("mif_conversion.out_file", "list_files.in2")],
            ),
            (dwi_wf, sinker, [("mif_conversion.out_file", "fmap")]),
        ]
    )
    return wf


def connect_tensor_wf(
    preproc_wf: pe.Workflow,
    sinker: Node,
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
            (
                dwi2tensor,
                sinker,
                [("out_file", "tensor")],
            ),
            (dwi2tensor, tensor2metrics, [("out_file", "in_file")]),
        ],
    )
    return wf
