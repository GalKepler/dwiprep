import os
from pathlib import Path
from bids import BIDSLayout
from typing import Union

DEFAULT_SYMLINK_DIR_NAME = "tmp"


def collect_data(
    bids_dir: Union[BIDSLayout, Path, str],
    participant_label: str,
    dwi_identifier: dict,
    fmap_identifier: dict,
    t1w_identifier: dict,
    t2w_identifier: dict,
    bids_validate: bool = True,
):
    """
    Collects processing-relevant files from a BIDS dataset

    Parameters
    ----------
    bids_dir : Union[BIDSLayout, Path, str]
        Either BIDSLayout or path-like object representing an existing BIDS-compatible dataset.
    participant_label : str
        String representing a subject existing within *bids_dir*.
    bids_validate : bool, optional
        Whether to validate *bids_dir*`s compatibility with the BIDS format, by default True

    Returns
    -------
    [type]
        [description]
    """
    if isinstance(bids_dir, BIDSLayout):
        layout = bids_dir
    else:
        layout = BIDSLayout(str(bids_dir), bids_validate)
    queries = {
        "fmap": {"datatype": "fmap"},
        "dwi": {"datatype": "dwi", "suffix": "dwi"},
        "t2w": {"datatype": "anat", "suffix": "T2w"},
        "t1w": {"datatype": "anat", "suffix": "T1w"},
    }
    identifiers = {
        "fmap": fmap_identifier,
        "dwi": dwi_identifier,
        "t2w": t2w_identifier,
        "t1w": t1w_identifier,
    }

    subj_data = {
        dtype: sorted(
            layout.get(
                return_type="file",
                subject=participant_label,
                extension=["nii", "nii.gz"],
                **query,
            )
        )
        for dtype, query in queries.items()
    }
    identified_subj_data = identify_data_types(subj_data, identifiers)

    symlinked_data = build_symlink_directory(identified_subj_data, bids_dir)

    return identified_subj_data, symlinked_data, layout


def build_symlink_directory(
    identified_subj_data: dict,
    bids_dir: Union[BIDSLayout, Path, str],
    symlink_dir: str = None,
):
    """
    Build a directory with symbolic links to subject's processing-relevant files,
    for better compatability with external tools.

    Parameters
    ----------
    bids_dir : Union[BIDSLayout, Path, str]
        Either BIDSLayout or path-like object representing an existing BIDS-compatible dataset.
    identified_subj_data : dict
        All files associated with relevant data types and identified by user-defined rules

    Returns
    -------
    dict
        Dictionary with keys as *identified_subj_data*, and values pointing to corresponding symbolic links.
    """
    if symlink_dir is None:
        symlink_dir = Path(bids_dir).parent / DEFAULT_SYMLINK_DIR_NAME
    symlink_dict = {}
    for key, value in identified_subj_data.items():
        if isinstance(value, list):
            symlink_dict[key] = [
                create_symlink(val, symlink_dir, bids_dir) for val in value
            ]
        else:
            symlink_dict[key] = create_symlink(value, symlink_dir, bids_dir)
    return symlink_dict


def create_symlink(
    source: Union[Path, str], symlink_dir: Path, bids_dir: Path
):
    """
    Creates a symbolic link to *source* in a specified directory *symlink_dir*
    Parameters
    ----------
    source : Union[Path, str]
        Path to a file in a BIDS-compatible directory
    symlink_dir : Path
        Path to the destination to create symbolic links in.

    Returns
    -------
    Path
        Path to the symbolic link pointing to *source*
    """
    source = Path(source)
    relative_path = str(source).replace(bids_dir, "")
    target = symlink_dir / Path(relative_path.strip("/"))

    source_related = [
        f for f in source.parent.glob(f"{source.name.split('.')[0]}*")
    ]
    for s in source_related:
        t = target.parent / s.name
        if not t.exists():
            t.symlink_to(source)
    return target


def identify_data_types(subj_data: dict, identifiers: dict):
    """
    Identify user-identified relevant files.

    Parameters
    ----------
    subj_data : dict
        All files associated with relevant data types
    identifiers : dict
        Dictionary describing rules for identifying specific relevant files according to BIDS-compatible keys

    Returns
    -------
    dict
        All files associated with relevant data types and identified by user-defined rules
    """
    identified_subj_data = {}
    for key, value in subj_data.items():
        rules = identifiers.get(key)
        if isinstance(value, list):
            identified_subj_data[key] = [
                val for val in value if validate_file(rules, val)
            ]
        else:
            identified_subj_data[key] = validate_file(rules, value)
    return identified_subj_data


def validate_file(rules: dict, fname: dict):
    """
    Validates files by BIDS-compatible identifiers
    Parameters
    ----------
    rules : dict
        Dictionary with keys of BIDS-recognized key and their accepted values.
    fname : str
        File to validate.
    """
    valid = []
    for key, value in rules.items():
        if f"{key}-{value}" in fname:
            valid.append(True)
        else:
            valid.append(False)
    return all(valid)
