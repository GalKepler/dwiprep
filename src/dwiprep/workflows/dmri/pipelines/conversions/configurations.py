"""
Configurations for *conversions* pipelines.
"""
MIF_INPUTNODE_FIELDS = [
    # DWI
    "dwi_file",
    "in_bvec",
    "in_bval",
    "dwi_json",
    # Fieldmaps
    "fmap_ap",
    "fmap_ap_json",
    "fmap_pa",
    "fmap_pa_json",
]
MIF_OUTPUTNODE_FIELDS = [
    "dwi_file",
    "fmap_ap",
    "fmap_pa",
]

NII_INPUTNODE_FIELDS = [
    # DWI
    "dwi_file",
    # SBRef
    "epi_ref",
]
NII_OUTPUTNODE_FIELDS = [
    "dwi_file",
    "dwi_bvec",
    "dwi_bval",
    "dwi_json",
    "epi_ref_file",
    "epi_ref_json",
]
