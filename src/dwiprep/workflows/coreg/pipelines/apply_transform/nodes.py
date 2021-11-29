"""
Nodes' configurations for *apply_transforms* pipelines.
"""
import nipype.pipeline.engine as pe
from nipype.interfaces import mrtrix3 as mrt
from nipype.interfaces import utility as niu

from dwiprep.workflows.coreg.pipelines.apply_transform.configurations import (
    APPLY_XFM_KWARGS,
    INPUT_NODE_FIELDS,
    OUTPUT_NODE_FIELDS,
    TRANSFORM_AFF_KWARGS,
)

#: i/o
INPUT_NODE = pe.Node(
    niu.IdentityInterface(fields=INPUT_NODE_FIELDS),
    name="inputnode",
)
OUTPUT_NODE = pe.Node(
    niu.IdentityInterface(fields=OUTPUT_NODE_FIELDS),
    name="outputnode",
)

#: Building blocks
TRANSFORM_FSL_AFF_TO_MRTRIX = pe.Node(
    mrt.TransformFSLConvert(**TRANSFORM_AFF_KWARGS), name="transformconvert"
)
APPLY_XFM_TENSOR_NODE = pe.MapNode(
    mrt.MRTransform(**APPLY_XFM_KWARGS),
    iterfield=["in_files"],
    name="mrtransform_tensor",
)
APPLY_XFM_DWI_NODE = pe.Node(
    mrt.MRTransform(**APPLY_XFM_KWARGS), name="apply_xfm_dwi"
)
