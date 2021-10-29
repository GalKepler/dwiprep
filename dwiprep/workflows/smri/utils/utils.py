import os
from pathlib import Path

PATH_LIKE_KWARGS = [
    "bids-filter-file",
    "fs-license-file",
    "fs-subjects-dir",
    "work-dir",
    "w",
]
FLAGS = (
    "skip_bids_validation",
    "low-mem",
    "boilerplate",
    "longitudinal",
    "skull-strip-fixed-seed",
    "no-submm-recon",
    "fs-no-reconall",
    "fast-track",
    "resource-monitor",
    "reports-only",
    "write-graph",
    "stop-on-first-crash",
    "notrack",
    "sloppy",
)

AUTOMATIC_KWARGS = {
    "participant_label": "participant_label",
    "work-dir": "work_dir",
    "bids-filter-file": "bids_filter_path",
}

ALLOWED_BIDS_ENTITIES = ["t1w", "t2w"]

DEFAULT_KWARGS = {"output-spaces": ["MNI152NLin2009cAsym", "anat"]}

OUTPUTS = {
    # Anatomicals
    "native_T1w": ["smriprep", "anat", "desc-preproc_T1w.nii.gz"],
    "native_brain_mask": ["smriprep", "anat", "desc-brain_mask.nii.gz"],
    "native_parcellation": ["smriprep", "anat", "*dseg.nii.gz"],
    "native_csf": ["smriprep", "anat", "label-CSF_probseg.nii.gz"],
    "native_gm": ["smriprep", "anat", "label-GM_probseg.nii.gz"],
    "native_wm": ["smriprep", "anat", "label-WM_probseg.nii.gz"],
    "standard_T1w": [
        "smriprep",
        "anat",
        "space-MNI152NLin2009cAsym_desc-preproc_T1w.nii.gz",
    ],
    "standard_brain_mask": [
        "smriprep",
        "anat",
        "space-MNI152NLin2009cAsym_desc-brain_mask.nii.gz",
    ],
    "standard_parcellation": [
        "smriprep",
        "anat",
        "space-MNI152NLin2009cAsym_dseg.nii.gz",
    ],
    "standard_csf": [
        "smriprep",
        "anat",
        "space-MNI152NLin2009cAsym_label-CSF_probseg.nii.gz",
    ],
    "standard_gm": [
        "smriprep",
        "anat",
        "space-MNI152NLin2009cAsym_label-GM_probseg.nii.gz",
    ],
    "standard_wm": [
        "smriprep",
        "anat",
        "space-MNI152NLin2009cAsym_label-WM_probseg.nii.gz",
    ],
    "native_to_mni_transform": [
        "smriprep",
        "anat",
        "from-T1w_to-MNI152NLin2009cAsym_mode-image_xfm.h5",
    ],
    "mni_to_native_transform": [
        "smriprep",
        "anat",
        "from-MNI152NLin2009cAsym_to-T1w_mode-image_xfm.h5",
    ],
    "native_to_fsnative_transform": [
        "smriprep",
        "anat",
        "from-T1w_to-fsnative_mode-image_xfm.txt",
    ],
    "fsnative_to_native_transform": [
        "smriprep",
        "anat",
        "from-fsnative_to-T1w_mode-image_xfm.txt",
    ],
    "smoothwm": ["smriprep", "anat", "hemi-*_smoothwm.surf.gii"],
    "pial": ["smriprep", "anat", "hemi-*_pial.surf.gii"],
    "midthickness": ["smriprep", "anat", "hemi-*_midthickness.surf.gii"],
    "inflated": ["smriprep", "anat", "hemi-*_inflated.surf.gii"],
    # Freesurfer
    "freesurfer_T1": ["freesurfer", "mri", "T1.mgz"],
    "freesurfer_rawavg": ["freesurfer", "mri", "rawavg.mgz"],
    "freesurfer_orig": ["freesurfer", "mri", "orig.mgz"],
    "freesurfer_nu": ["freesurfer", "mri", "nu.mgz"],
    "freesurfer_norm": ["freesurfer", "mri", "norm.mgz"],
    "freesurfer_aseg": ["freesurfer", "mri", "aseg.mgz"],
    "freesurfer_aseg_stats": ["freesurfer", "stats", "aseg.stats"],
    "freesurfer_brain": ["freesurfer", "mri", "brain.mgz"],
    "freesurfer_brainmask": ["freesurfer", "mri", "brainmask.mgz"],
    "freesurfer_filled": ["freesurfer", "mri", "filled.mgz"],
    "freesurfer_wm": ["freesurfer", "mri", "wm.mgz"],
    "freesurfer_wmparc": ["freesurfer", "mri", "wmparc.mgz"],
    "freesurfer_wmparc_stats": ["freesurfer", "stats", "wmparc.stats"],
    "freesurfer_BA_stats": ["freesurfer", "stats", ".BA_exvivo*.stats"],
    # TODO: Finish outputs dictionary.
}


def validate_queries(queries: dict) -> dict:
    """
    Some BIDS entities are not acceptable for querying using *smriprep*.
    This function validates that the queries defined by the user are allowed.

    Parameters
    ----------
    queries : dict
        Entity (dwi|t1w|t2w|flair|etc.) and its corresponding pattern for identification.

    Returns
    -------
    dict
        Dictionary with keys of only *smriprep*-allowed entities.
    """
    return {
        key: value
        for key, value in queries.items()
        if key in ALLOWED_BIDS_ENTITIES
    }


def locate_fs_license_file():
    fs_home = os.environ.get("FREESURFER_HOME")
    fs_license = Path(fs_home) / "license.txt"
    return fs_license if fs_license.exists() else None
