from nipype.interfaces import mrtrix3 as mrt
from nipype import Node, Function
from typing import Tuple
from pathlib import Path

KWARGS_BY_FILE_TYPES = {
    "nifti": "in_file",
    "bval": "in_bval",
    "bvec": "in_bvec",
    "json": "json_import",
}

MAP_KWARGS_TO_SUFFIXES = {
    "json_import": ["json"],
    "in_bval": ["bval"],
    "in_bvec": ["bvec"],
    "in_file": ["nii", "nii.gz"],
}


def map_list_to_kwargs(
    file_names: list, mapping: dict = MAP_KWARGS_TO_SUFFIXES
):
    """
    Maps a list of files to their corresponding *mrconvert* inputs kwargs.

    Parameters
    ----------
    file_names : list
        A list of existing files.

    Returns
    -------
    Tuple[str, str, str, str]
        Four sorted outputs: *in_file*,*json*,*bvec*,*bval*
    """

    out_dict = {}
    for file_name in file_names:
        suffixes = Path(file_name).suffixes
        suffix = "".join(suffixes).lstrip(".")
        for key, val in mapping.items():
            if suffix in val:
                out_dict[key] = file_name
    return out_dict


def mrconvert(kwargs: dict) -> mrt.MRConvert:
    """
    Build mrtrix3's *mrconvert* function by keyword arguemnts

    Parameters
    ----------
    kwargs : dict
        Dictionary with kwargs as keys

    Returns
    -------
    mrt.MRConvert
        An MRConvert instance predefined using *kwargs*
    """
    return mrt.MRConvert(**kwargs)


def mrconvert_map_types_to_kwargs(parsed_files: dict) -> dict:
    """
    Map previously parsed (by file types) to their corresponding keyword arguments in *mrconvert*

    Parameters
    ----------
    parsed_files : dict
        Dictionary with keys of file types.

    Returns
    -------
    dict
        Dictionary with keys of keyword arguments.
    """
    files_by_kwargs = {}
    for key, value in parsed_files.items():
        kwarg = KWARGS_BY_FILE_TYPES.get(key)
        files_by_kwargs[kwarg] = value
    return files_by_kwargs
