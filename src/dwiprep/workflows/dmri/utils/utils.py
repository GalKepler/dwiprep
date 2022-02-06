from pathlib import Path
from typing import Union

import nipype.pipeline.engine as pe
from bids import BIDSLayout
from nipype import Function, Workflow

MANDATORY_ENTITIES = ["dwi"]

RECOMMENDED_ENTITIES = ["fmap"]

RELEVANT_DATA_TYPES = ["dwi", "fmap"]

WORK_DIR_NAME = "dmriprep_wf"

OUTPUT_ENTITIES = {"raw_mif": {"description": "orig", "extension": "mif"}}

OUTPUT_PATTERNS = "sub-{subject}/[ses-{session}/][{datatype}/]sub-{subject}[_ses-{session}][_acq-{acquisition}][_dir-{direction}][_space-{space}][_desc-{description}]_{suffix}.{extension}"

STARTING_TEMPLATES = {
    "dwi": "dwi/sub-%s*desc-orig*dwi.mif",
    "fmap": "fmap/sub-%s*desc-orig*.mif",
}

OUTPUTS = {
    # Anatomicals
    "native_T1w": ["dmriprep", "anat", "desc-preproc_T1w.nii.gz"],
    "native_brain_mask": ["dmriprep", "anat", "desc-brain_mask.nii.gz"],
    "native_parcellation": ["dmriprep", "anat", "*dseg.nii.gz"],
    "native_csf": ["dmriprep", "anat", "label-CSF_probseg.nii.gz"],
    "native_gm": ["dmriprep", "anat", "label-GM_probseg.nii.gz"],
    "native_wm": ["dmriprep", "anat", "label-WM_probseg.nii.gz"],
    "standard_T1w": [
        "dmriprep",
        "anat",
        "space-MNI152NLin2009cAsym_desc-preproc_T1w.nii.gz",
    ],
    "standard_brain_mask": [
        "dmriprep",
        "anat",
        "space-MNI152NLin2009cAsym_desc-brain_mask.nii.gz",
    ],
    "standard_parcellation": [
        "dmriprep",
        "anat",
        "space-MNI152NLin2009cAsym_dseg.nii.gz",
    ],
    "standard_csf": [
        "dmriprep",
        "anat",
        "space-MNI152NLin2009cAsym_label-CSF_probseg.nii.gz",
    ],
    "standard_gm": [
        "dmriprep",
        "anat",
        "space-MNI152NLin2009cAsym_label-GM_probseg.nii.gz",
    ],
    "standard_wm": [
        "dmriprep",
        "anat",
        "space-MNI152NLin2009cAsym_label-WM_probseg.nii.gz",
    ],
    "native_to_mni_transform": [
        "dmriprep",
        "anat",
        "from-T1w_to-MNI152NLin2009cAsym_mode-image_xfm.h5",
    ],
    "mni_to_native_transform": [
        "dmriprep",
        "anat",
        "from-MNI152NLin2009cAsym_to-T1w_mode-image_xfm.h5",
    ],
    "native_to_fsnative_transform": [
        "dmriprep",
        "anat",
        "from-T1w_to-fsnative_mode-image_xfm.txt",
    ],
    "fsnative_to_native_transform": [
        "dmriprep",
        "anat",
        "from-fsnative_to-T1w_mode-image_xfm.txt",
    ],
    "smoothwm": ["dmriprep", "anat", "hemi-*_smoothwm.surf.gii"],
    "pial": ["dmriprep", "anat", "hemi-*_pial.surf.gii"],
    "midthickness": ["dmriprep", "anat", "hemi-*_midthickness.surf.gii"],
    "inflated": ["dmriprep", "anat", "hemi-*_inflated.surf.gii"],
    # dmri
    "native_preproc_dwi_nii": [
        "dmriprep",
        "dwi",
        "dir-*space-orig_desc-preproc_dwi.nii.gz",
    ],
    "native_preproc_dwi_json": [
        "dmriprep",
        "dwi",
        "*space-orig_desc-preproc_dwi.json",
    ],
    "native_preproc_dwi_bvec": [
        "dmriprep",
        "dwi",
        "*space-orig_desc-preproc_dwi.bvec",
    ],
    "native_preproc_dwi_bval": [
        "dmriprep",
        "dwi",
        "*space-orig_desc-preproc_dwi.bval",
    ],
    "native_preproc_epi_ref_file": [
        "dmriprep",
        "dwi",
        "*space-orig_desc-preproc_epiref.nii.gz",
    ],
    "native_preproc_epiref_json": [
        "dmriprep",
        "dwi",
        "*space-orig_desc-preproc_epiref.json",
    ],
    "coreg_preproc_dwi_nii": [
        "dmriprep",
        "dwi",
        "*space-anat_desc-preproc_dwi.nii.gz",
    ],
    "coreg_preproc_dwi_bvec": [
        "dmriprep",
        "dwi",
        "*space-anat_desc-preproc_dwi.bvec",
    ],
    "coreg_preproc_dwi_bval": [
        "dmriprep",
        "dwi",
        "*space-anat_desc-preproc_dwi.bval",
    ],
    "coreg_preproc_dwi_json": [
        "dmriprep",
        "dwi",
        "*space-anat_desc-preproc_dwi.json",
    ],
    "coreg_preproc_epiref_nii": [
        "dmriprep",
        "dwi",
        "*space-anat_desc-preproc_epiref.nii.gz",
    ],
    "native_to_anat_transform": [
        "dmriprep",
        "dwi",
        "*from-epiref_to-T1w_mode-image_xfm.txt",
    ],
    "anat_to_native_transform": [
        "dmriprep",
        "dwi",
        "*from-epiref_to-T1w_mode-image_xfm.txt",
    ],
    "phasediff_fmap_nii": [
        "dmriprep",
        "fmap",
        "_desc-phasediff_fieldmap.nii.gz",
    ],
    "phasediff_fmap_json": [
        "dmriprep",
        "fmap",
        "desc-phasediff_fieldmap.json",
    ],
    "native_fa": [
        "dmriprep",
        "dwi",
        "*space-orig_desc-fa_epiref.nii.gz",
    ],
    "native_adc": [
        "dmriprep",
        "dwi",
        "*space-orig_desc-adc_epiref.nii.gz",
    ],
    "native_ad": [
        "dmriprep",
        "dwi",
        "*space-orig_desc-ad_epiref.nii.gz",
    ],
    "native_rd": [
        "dmriprep",
        "dwi",
        "*space-orig_desc-rd_epiref.nii.gz",
    ],
    "native_cl": [
        "dmriprep",
        "dwi",
        "*space-orig_desc-cl_epiref.nii.gz",
    ],
    "native_cp": [
        "dmriprep",
        "dwi",
        "*space-orig_desc-cp_epiref.nii.gz",
    ],
    "native_cs": [
        "dmriprep",
        "dwi",
        "*space-orig_desc-cs_epiref.nii.gz",
    ],
    "native_evec": [
        "dmriprep",
        "dwi",
        "*space-orig_desc-evec_epiref.nii.gz",
    ],
    "native_eval": [
        "dmriprep",
        "dwi",
        "*space-orig_desc-eval_epiref.nii.gz",
    ],
    "coreg_fa": [
        "dmriprep",
        "dwi",
        "*space-anat_desc-fa_epiref.nii.gz",
    ],
    "coreg_adc": [
        "dmriprep",
        "dwi",
        "*space-anat_desc-adc_epiref.nii.gz",
    ],
    "coreg_ad": [
        "dmriprep",
        "dwi",
        "*space-anat_desc-ad_epiref.nii.gz",
    ],
    "coreg_rd": [
        "dmriprep",
        "dwi",
        "*space-anat_desc-rd_epiref.nii.gz",
    ],
    "coreg_cl": [
        "dmriprep",
        "dwi",
        "*space-anat_desc-cl_epiref.nii.gz",
    ],
    "coreg_cp": [
        "dmriprep",
        "dwi",
        "*space-anat_desc-cp_epiref.nii.gz",
    ],
    "coreg_cs": [
        "dmriprep",
        "dwi",
        "*space-anat_desc-cs_epiref.nii.gz",
    ],
    "coreg_evec": [
        "dmriprep",
        "dwi",
        "*space-anat_desc-evec_epiref.nii.gz",
    ],
    "coreg_eval": [
        "dmriprep",
        "dwi",
        "*space-anat_desc-eval_epiref.nii.gz",
    ],
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
}


def infer_phase_encoding_direction(
    layout: BIDSLayout, file_name: Union[Path, str]
) -> str:
    """
    Used *layout* to query the phase encoding direction used for *file_name* in <x,j,z> format.

    Parameters
    ----------
    layout : BIDSLayout
        An instantiated BIDSLayout
    file_name : Union[Path,str]
        DWI series to query

    Returns
    -------
    str
        Phase encoding direction.
    """
    bids_file = layout.get_file(file_name)
    if not bids_file:
        raise FileNotFoundError(
            "A valid DWI series must be provided to infer phase encoding direction!"
        )
    return bids_file.get_metadata().get("PhaseEncodingDirection")


def get_output_path_node(name: str):
    return pe.Node(
        Function(
            input_names=["bids_dir", "destination", "source", "entities"],
            output_names=["out_file"],
            function=build_output_path,
        ),
        name=name,
    )


def add_output_nodes(
    input_node: pe.Node,
    source_key: str,
    output_kwargs: dict,
    target_node: pe.Node,
    node_name: str,
):
    connected_nodes = []
    for key, value in output_kwargs.items():
        output_node = get_output_path_node(f"{node_name}_{key}_namer")
        output_node.inputs.entities = value
        connected_nodes.append(
            (input_node, output_node, [(source_key, "source")])
        )
        connected_nodes.append(
            (
                input_node,
                output_node,
                [("bids_dir", "bids_dir"), ("destination", "destination")],
            ),
        )
        connected_nodes.append((output_node, target_node, [("out_file", key)]))
    return connected_nodes


def build_output_path(
    bids_dir: str, destination: str, source: str, entities: dict = {}
):
    OUTPUT_PATTERNS = "sub-{subject}/[ses-{session}/][{datatype}/]sub-{subject}[_ses-{session}][_acq-{acquisition}][_dir-{direction}][_space-{space}][_desc-{description}]_{suffix}.{extension}"
    from pathlib import Path

    from bids import BIDSLayout

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


def infer_phase_encoding_direction_mif(in_file: str) -> str:
    """
    Utilizes *mrinfo* for a specific query of phase encoding direction.

    Parameters
    ----------
    in_file : str
        File to query

    Returns
    -------
    str
        Phase Encoding Direction as denoted in *in_file*`s header.
    """
    import subprocess

    return (
        subprocess.check_output(
            ["mrinfo", str(in_file), "-property", "PhaseEncodingDirection"]
        )
        .decode("utf-8")
        .replace("\n", "")
    )


def check_opposite_phase_encoding(layout: BIDSLayout, fmap: list, dwi: list):
    """
    Checks whether to extract mean B0 image from DWI series and use it for SDC.

    Parameters
    ----------
    layout : BIDSLayout
        BIDSLayout instance describing a valid dataset
    fmap : list
        List of files that are associated with the fieldmap.
    dwi : list
        List of files that are associated with the DWI series.

    Returns
    -------
    bool
        Whether to extract B0 image and run SDC.
    """
    extract_b0 = True
    run_sdc = True
    fmap = [f for f in fmap if ".nii" in Path(f).name]
    dwi = [f for f in dwi if ".nii" in Path(f).name]
    fmap_directions = [infer_phase_encoding_direction(layout, f) for f in fmap]

    if len(set(fmap_directions)) > 1:
        extract_b0 = False

    dwi_directions = [infer_phase_encoding_direction(layout, f) for f in dwi]
    if len(set(dwi_directions + fmap_directions)) < 2:
        extract_b0 = False
        run_sdc = False
    return extract_b0, run_sdc


def get_relevant_files(session_data: dict):
    """
    Generates the pipeline's "starting node"

    Parameters
    ----------
    session_data : dict
        A dictionary with the locations of all necessary session's data

    Returns
    -------
    str,str
        The "starting" node for processing
    """
    return session_data.get("dwi"), session_data.get("fmap")
