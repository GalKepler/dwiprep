import nipype.pipeline.engine as pe
import nipype.interfaces.utility as niu

INPUTNODE = pe.Node(
    niu.IdentityInterface(
        fields=[
            "output_dir",
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
            # From anatomical
            "t1w_preproc",
            "t1w_mask",
            "t1w_dseg",
            "t1w_aseg",
            "t1w_aparc",
            "t1w_tpms",
            "template",
            "anat2std_xfm",
            "std2anat_xfm",
            "subjects_dir",
            "subject_id",
            "t1w2fsnative_xfm",
            "fsnative2t1w_xfm",
        ]
    ),
    name="inputnode",
)
