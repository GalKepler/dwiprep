"""
Nodes' configurations for *epi_eg* pipelines.
"""
import nipype.pipeline.engine as pe
from nipype.interfaces import utility as niu
from nipype.interfaces import mrtrix3 as mrt

from dwiprep.workflows.dmri.pipelines.fmap_prep.configurations import (
    INPUT_NODE_FIELDS,
    OUTPUT_NODE_FIELDS,
    MERGE_KWARGS,
    MRCAT_KWARGS,
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
MERGE_NODE = pe.Node(niu.Merge(**MERGE_KWARGS), name="merge_files")

MRCAT_NODE = pe.Node(
    mrt.MRCat(**MRCAT_KWARGS),
    name="mrcat",
)
