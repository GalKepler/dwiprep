"""
Nodes' configurations for *apply_transforms* pipelines.
"""
import nipype.pipeline.engine as pe
from nipype.interfaces import utility as niu
from nipype.interfaces import fsl

from dwiprep.workflows.coreg.pipelines.apply_transform.configurations import (
    INPUT_NODE_FIELDS,
    OUTPUT_NODE_FIELDS,
    APPLY_XFM_KWARGS,
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
APPLY_XFM_TENSOR_NODE = pe.MapNode(
    fsl.ApplyXFM(**APPLY_XFM_KWARGS),
    iterfield=["in_file"],
    name="apply_xfm_tensor",
)
APPLY_XFM_DWI_NODE = pe.Node(
    fsl.ApplyXFM(**APPLY_XFM_KWARGS), name="apply_xfm_dwi"
)
