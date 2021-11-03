import os

EXTRACT_B0_COMMAND = (
    "dwiextract {in_file} - -bzero | mrmath - mean {out_file} -axis 3"
)


def dwiextract(kwargs: dict):
    """[summary]

    Parameters
    ----------
    file_name : Union[Path,str]
        [description]
    """
    cmd = EXTRACT_B0_COMMAND.format(**kwargs)
    print(cmd)
    os.system(EXTRACT_B0_COMMAND.format(**kwargs))
