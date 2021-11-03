from nipype.interfaces.mrtrix3.utils import MRConvert
from nipype.interfaces.utility.base import IdentityInterface
import nipype.pipeline.engine as pe
from nipype import Function
import nipype.interfaces.io as nio
import nipype.interfaces.mrtrix3 as mrt
from nipype.interfaces.utility import Merge, IdentityInterface
from nipype.pipeline.engine.workflows import Workflow
from dwiprep.workflows.dmri.utils.utils import (
    OUTPUT_PATTERNS,
    infer_phase_encoding_direction_mif,
    get_output_path_node,
    add_output_nodes,
)
from dwiprep.interfaces.mrconvert import map_list_to_kwargs, parse_dict_by_keys

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

MRCONVERT_KWARGS = {
    "inputs": {"args": "-force"},
    "outputs": {"out_file": {"description": "orig", "extension": "mif"}},
}


def get_inputnode():
    return pe.Node(
        IdentityInterface(
            fields=[
                # participant's info
                "participant_label",
                "session_id",
                # Execution info
                "bids_dir",
                "work_dir",
                "destination",
                # DWI
                "dwi",
                "in_bvec",
                "in_bval",
                "in_json",
                # fmap
                "fmap_ap",
                "fmap_ap_json",
                "fmap_pa",
                "fmap_pa_json",
            ]
        ),
        name="inputnode",
    )


def build_single_conversion_node(data_type: str):
    wf = Workflow(name=f"{data_type}_converter")

    mrconvert_node = pe.Node(mrt.MRConvert(), name=f"mrconvert")
    output_node = get_output_path_node()
    wf.connect([(mrconvert_node, output_node, [("in_file", "source")])])


def build_conversion_nodes(
    inputnode: pe.Node,
    run_data: dict,
    mrconvert_kwargs: dict = MRCONVERT_KWARGS,
):
    nodes = {}
    connectors = {}
    for key in ["dwi", "fmap_ap", "fmap_pa"]:
        if not run_data.get(key):
            continue
        target_node = pe.Node(
            mrt.MRConvert(**mrconvert_kwargs.get("inputs")),
            name=f"{key}_conversion",
        )
        nodes[key] = target_node
        connectors[key] = add_output_nodes(
            inputnode, key, mrconvert_kwargs.get("outputs"), target_node, key
        )
    return nodes, connectors


def generate_conversion_workflow(
    inputnode: pe.Node,
    run_data: dict,
    mrconvert_kwargs: dict = MRCONVERT_KWARGS,
):
    wf = Workflow(name="conversion")
    nodes, output_connectors = build_conversion_nodes(
        inputnode, run_data, mrconvert_kwargs
    )
    dwi_node, fmap_ap_node, fmap_pa_node = [
        nodes.get(key) for key in ["dwi", "fmap_ap", "fmap_pa"]
    ]

    base_connector = [
        (
            inputnode,
            dwi_node,
            [
                ("dwi", "in_file"),
                ("in_json", "json_import"),
                ("in_bvec", "in_bvec"),
                ("in_bval", "in_bval"),
            ],
        )
    ]
    for connector in output_connectors.get("dwi"):
        base_connector.append(connector)
    if fmap_pa_node:
        base_connector.append(
            (
                inputnode,
                fmap_pa_node,
                [
                    ("fmap_pa", "in_file"),
                    ("fmap_pa_json", "json_import"),
                ],
            )
        )
        for connector in output_connectors.get("fmap_pa"):
            base_connector.append(connector)
    if fmap_ap_node:
        base_connector.append(
            (
                inputnode,
                fmap_ap_node,
                [
                    ("fmap_ap", "in_file"),
                    ("fmap_ap_json", "json_import"),
                ],
            )
        )
        for connector in output_connectors.get("fmap_ap"):
            base_connector.append(connector)
    wf.connect(base_connector)
    wf.base_dir = inputnode.inputs.work_dir
    wf.write_graph(graph2use="colored")
    return wf


def get_output_path_node(name: str):
    return pe.Node(
        Function(
            input_names=["bids_dir", "destination", "source", "entities"],
            output_names=["out_file"],
        ),
        name=name,
    )


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
        target_entities[key] = val
    output = Path(destination) / layout.build_path(
        target_entities,
        path_patterns=OUTPUT_PATTERNS,
        validate=False,
        absolute_paths=False,
    )
    output.parent.mkdir(exist_ok=True, parents=True)

    return str(output)


def build_epi_ref_wf(
    inputnode: pe.Node,
    dwiextract_kwargs: dict = DWIEXTRACT_KWARGS,
    mrmath_kwargs: dict = MRMATH_KWARGS,
) -> Workflow:
    """
    Build a workflow for generation of EPI referance image

    Parameters
    ----------
    inputnode : pe.Node
        Pipeline's input node

    Returns
    -------
    Workflow
        EPI-reference generation workflow
    """
    connections = []
    dwiextract = pe.Node(
        mrt.DWIExtract(**dwiextract_kwargs.get("inputs")), name="dwiextract"
    )
    dwiextract_outputs_connection = add_output_nodes(
        inputnode,
        "dwi",
        dwiextract_kwargs.get("outputs"),
        dwiextract,
        "dwiextract",
    )
    for connection in dwiextract_outputs_connection:
        connections.append(connection)
    mrmath = pe.Node(mrt.MRMath(**mrmath_kwargs.get("inputs")), name="mrmath")
    mrmath_outputs_connection = add_output_nodes(
        inputnode,
        "dwi",
        mrmath_kwargs.get("outputs"),
        mrmath,
        "mrmath",
    )
    for connection in mrmath_outputs_connection:
        connections.append(connection)
    connections.append(
        (
            dwiextract,
            mrmath,
            [("out_file", "in_file")],
        )
    )
    wf = Workflow(name="EPI_ref")
    wf.connect(connections)
    wf.base_dir = inputnode.inputs.work_dir
    wf.write_graph(graph2use="colored")
    return wf


def add_phasediff_node(main_workflow: Workflow):
    inputnode = main_workflow.get_node("conversion.inputnode")
    merge_node = pe.Node(Merge(numinputs=2), name="merge_files")
    fmap_ap, fmap_pa = [
        getattr(inputnode.inputs, key, None) for key in ["fmap_ap", "fmap_pa"]
    ]
    if fmap_ap and fmap_pa:
        connection = [
            (
                main_workflow.get_node("conversion"),
                merge_node,
                [("fmap_ap_conversion.out_file", "in1")],
            ),
            (
                main_workflow.get_node("conversion"),
                merge_node,
                [("fmap_pa_conversion.out_file", "in2")],
            ),
        ]
        fmap = "fmap_pa"
    else:
        if fmap_ap:
            connection = [
                (
                    main_workflow.get_node("conversion"),
                    merge_node,
                    [("fmap_ap_conversion.out_file", "in1")],
                ),
                (
                    main_workflow.get_node("EPI_ref"),
                    merge_node,
                    [("mrmath.out_file", "in2")],
                ),
            ]
            fmap = "fmap_ap"
        elif fmap_pa:
            connection = [
                (
                    main_workflow.get_node("conversion"),
                    merge_node,
                    [("fmap_pa_conversion.out_file", "in1")],
                ),
                (
                    main_workflow.get_node("EPI_ref"),
                    merge_node,
                    [("mrmath.out_file", "in2")],
                ),
            ]
            fmap = "fmap_pa"
        else:
            raise NotImplementedError(
                "Currently fieldmap-based SDC is mandatory and thus requires at least on opposite single-volume EPI image."
            )
    main_workflow.connect(connection)
    return fmap, merge_node


def build_backbone(
    conversion_wf: Workflow,
    dwiextract_kwargs: dict = DWIEXTRACT_KWARGS,
    mrmath_kwargs: dict = MRMATH_KWARGS,
    mrcat_kwargs: dict = MRCAT_KWARGS,
    dwidenoise_kwargs: dict = DWIDENOISE_KWARGS,
    dwifslpreproc_kwargs: dict = DWIFSLPREPROC_KWARGS,
    dwibiascorrect_kwargs: dict = DWIBIASCORRECT_KWARGS,
) -> Workflow:
    main_workflow = Workflow(name="dMRIprep")
    inputnode = conversion_wf.get_node("inputnode")
    main_workflow.base_dir = inputnode.inputs.work_dir
    epi_ref_wf = build_epi_ref_wf(inputnode, dwiextract_kwargs, mrmath_kwargs)
    main_workflow.connect(
        [
            (
                conversion_wf,
                epi_ref_wf,
                [("dwi_conversion.out_file", "dwiextract.in_file")],
            ),
        ]
    )
    fmap, merge_node = add_phasediff_node(main_workflow)
    preprocess_wf = init_preprocess_wf(
        inputnode,
        fmap,
        mrcat_kwargs,
        dwidenoise_kwargs,
        dwifslpreproc_kwargs,
        dwibiascorrect_kwargs,
    )
    main_workflow.connect(
        [
            (
                conversion_wf,
                preprocess_wf,
                [("dwi_conversion.out_file", "dwidenoise.in_file")],
            ),
            (
                merge_node,
                preprocess_wf,
                [("out", "mrcat.in_files")],
            ),
        ]
    )
    return main_workflow


def connect_tensor_wf(
    inputnode: pe.Node,
    main_workflow: Workflow,
    dwi2tensor_kwargs: dict = DWI2TENSOR_KWARGS,
    tensor2metrics_kwargs: dict = TENSOR2METRICS_KWARGS,
):
    preproc_wf = main_workflow.get_node("preprocess")
    tensor_wf = build_tensor_wf(
        inputnode, dwi2tensor_kwargs, tensor2metrics_kwargs
    )
    main_workflow.connect(
        [
            (
                preproc_wf,
                tensor_wf,
                [("biascorrect.out_file", "dwi2tensor.in_file")],
            ),
        ]
    )
    return main_workflow


def init_preprocess_wf(
    inputnode: pe.Node,
    fmap: str,
    mrcat_kwargs: dict = MRCAT_KWARGS,
    dwidenoise_kwargs: dict = DWIDENOISE_KWARGS,
    dwifslpreproc_kwargs: dict = DWIFSLPREPROC_KWARGS,
    dwibiascorrect_kwargs: dict = DWIBIASCORRECT_KWARGS,
):
    wf = pe.Workflow(name="preprocess")
    wf.base_dir = inputnode.inputs.work_dir

    connections = []

    # mrcat
    mrcat = pe.Node(mrt.MRCat(**mrcat_kwargs.get("inputs")), name="mrcat")
    mrcat_outputs_connection = add_output_nodes(
        inputnode,
        fmap,
        mrcat_kwargs.get("outputs"),
        mrcat,
        "mrcat",
    )
    for connection in mrcat_outputs_connection:
        connections.append(connection)

    # dwidenoise
    dwidenoise = pe.Node(
        mrt.DWIDenoise(**dwidenoise_kwargs.get("inputs")), name="dwidenoise"
    )
    dwidenoise_outputs_connection = add_output_nodes(
        inputnode,
        "dwi",
        dwidenoise_kwargs.get("outputs"),
        dwidenoise,
        "dwidenoise",
    )
    for connection in dwidenoise_outputs_connection:
        connections.append(connection)

    # dwifslpreproc
    dwifslpreproc = pe.Node(
        mrt.DWIPreproc(**dwifslpreproc_kwargs.get("inputs")),
        name="dwifslpreproc",
    )
    dwifslpreproc_outputs_connection = add_output_nodes(
        inputnode,
        "dwi",
        dwifslpreproc_kwargs.get("outputs"),
        dwifslpreproc,
        "dwifslpreproc",
    )
    for connection in dwifslpreproc_outputs_connection:
        connections.append(connection)

    infer_pe = pe.Node(
        Function(
            input_names=["in_file"],
            output_names=["pe_dir"],
            function=infer_phase_encoding_direction_mif,
        ),
        name="infer_pe",
    )

    # biascorrect
    biascorrect = pe.Node(
        mrt.DWIBiasCorrect(**dwibiascorrect_kwargs.get("inputs")),
        name="biascorrect",
    )
    biascorrect_outputs_connection = add_output_nodes(
        inputnode,
        "dwi",
        dwibiascorrect_kwargs.get("outputs"),
        biascorrect,
        "biascorrect",
    )
    for connection in biascorrect_outputs_connection:
        connections.append(connection)

    connections.append(
        (dwidenoise, infer_pe, [("out_file", "in_file")]),
    )
    connections.append((infer_pe, dwifslpreproc, [("pe_dir", "pe_dir")]))
    connections.append((dwidenoise, dwifslpreproc, [("out_file", "in_file")]))
    connections.append((mrcat, dwifslpreproc, [("out_file", "in_epi")]))
    connections.append((dwifslpreproc, biascorrect, [("out_file", "in_file")]))

    wf.connect(connections)
    return wf


def build_tensor_wf(
    inputnode: pe.Node,
    dwi2tensor_kwargs: dict = DWI2TENSOR_KWARGS,
    tensor2metrics_kwargs: dict = TENSOR2METRICS_KWARGS,
):
    wf = pe.Workflow(name="tesnor_estimation")
    wf.base_dir = inputnode.inputs.work_dir

    connections = []

    # dwi2tensor
    dwi2tensor = pe.Node(
        mrt.FitTensor(**dwi2tensor_kwargs.get("inputs")), name="dwi2tensor"
    )
    dwi2tensor_outputs_connection = add_output_nodes(
        inputnode,
        "dwi",
        dwi2tensor_kwargs.get("outputs"),
        dwi2tensor,
        "dwi2tensor",
    )
    for connection in dwi2tensor_outputs_connection:
        connections.append(connection)

    # tensor2metrics
    tensor2metrics = pe.Node(
        mrt.TensorMetrics(**tensor2metrics_kwargs.get("inputs")),
        name="tensor2metrics",
    )
    tensor2metrics_outputs_connection = add_output_nodes(
        inputnode,
        "dwi",
        tensor2metrics_kwargs.get("outputs"),
        tensor2metrics,
        "tensor2metrics",
    )
    for connection in tensor2metrics_outputs_connection:
        connections.append(connection)

    connections.append((dwi2tensor, tensor2metrics, [("out_file", "in_file")]))
    wf.connect(connections)
    return wf
