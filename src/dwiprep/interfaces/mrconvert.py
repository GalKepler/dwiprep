from nipype.interfaces import mrtrix3 as mrt
import os

KWARGS_BY_FILE_TYPES = {
    "nifti": "in_file",
    "bval": "in_bval",
    "bvec": "in_bvec",
    "json": "json_import",
}


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
