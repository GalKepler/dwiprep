"""
Nodes' configurations for *conversions* pipelines.
"""
import nipype.pipeline.engine as pe
from nipype.interfaces import mrtrix3 as mrt
from nipype.interfaces import utility as niu

from dwiprep.workflows.dmri.pipelines.conversions.configurations import (
    MIF_INPUTNODE_FIELDS,
    MIF_OUTPUTNODE_FIELDS,
    NII_INPUTNODE_FIELDS,
    NII_OUTPUTNODE_FIELDS,
)

MIF_INPUT_NODE = pe.Node(
    niu.IdentityInterface(fields=MIF_INPUTNODE_FIELDS),
    name="inputnode",
)
MIF_OUTPUT_NODE = pe.Node(
    niu.IdentityInterface(fields=MIF_OUTPUTNODE_FIELDS),
    name="outputnode",
)
MIF_DWI_CONVERSION_NODE = pe.Node(mrt.MRConvert(), name="dwi_conversion")
MIF_FMAP_AP_CONVERSION_NODE = pe.Node(
    mrt.MRConvert(), name="fmap_ap_conversion"
)
MIF_FMAP_PA_CONVERSION_NODE = pe.Node(
    mrt.MRConvert(), name="fmap_pa_conversion"
)
NII_INPUT_NODE = pe.Node(
    niu.IdentityInterface(fields=NII_INPUTNODE_FIELDS),
    name="inputnode",
)
NII_OUTPUT_NODE = pe.Node(
    niu.IdentityInterface(fields=NII_OUTPUTNODE_FIELDS),
    name="outputnode",
)
NII_PREPROC_DWI_CONVERSION_NODE = pe.Node(
    mrt.MRConvert(
        out_file="dwi.nii.gz",
        out_bvec="dwi.bvec",
        out_bval="dwi.bval",
        json_export="dwi.json",
    ),
    name="preproc_conversion",
)
NII_COREG_DWI_CONVERSION_NODE = pe.Node(
    mrt.MRConvert(
        out_file="dwi.nii.gz",
        out_bvec="dwi.bvec",
        out_bval="dwi.bval",
        json_export="dwi.json",
    ),
    name="dwi_coreg_conversion",
)
NII_PREPROC_SBREF_CONVERSION_NODE = pe.Node(
    mrt.MRConvert(out_file="sbref.nii.gz", json_export="sbref.json"),
    name="preproc_sbref_conversion",
)
NII_PHASEDIFF_CONVERSION_NODE = pe.Node(
    mrt.MRConvert(out_file="phasediff.nii.gz", json_export="phasediff.json"),
    name="phasediff_conversion",
)
