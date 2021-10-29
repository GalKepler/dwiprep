import json
import os
import re
from typing import Union, Any
from pathlib import Path
from bids import BIDSLayout
from dwiprep.workflows.smri.utils.smriprep import (
    PATH_LIKE_KWARGS,
    DEFAULT_KWARGS,
    locate_fs_license_file,
    validate_queries,
)


class SmriprepManager(object):
    __version__ = "0.8.1"
    IMAGE_TEMPLATE = "{image_location}/smriprep:{version}.simg"
    DEFAULT_IMAGE_LOCATION = Path("/my_images")
    AUTOMATIC_KWARGS = {
        "--participant_label": "participant_label",
        "--work-dir": "work_dir",
        "--bids-filter-file": "bids_filter_path",
    }

    COMMAND_MOUNT_TEMPLATE = "singularity run --cleanenv -B {bids_dir}:/bids_dir -B {out_dir}:/out_dir"
    COMMMAND_TEMPLATE = (
        "{mounted_command} {image_path} /bids_dir /out_dir participant"
    )

    def __init__(
        self,
        bids_dir: Union[BIDSLayout, Path, str],
        out_dir: Union[Path, str],
        queries: dict,
        participant_label: str = None,
        image_path: str = None,
        run_kwargs: dict = DEFAULT_KWARGS,
        work_dir: Path = None,
    ):
        """

        Parameters
        ----------
        bids_dir : Union[Path, str]
            Either BIDSLayout or path-like object representing an existing BIDS-compatible dataset.
        out_dir : Union[Path, str]
            Path to smriprep's outputs
        queries : dict
            Dictionary describing specific localization of different entities in a BIDS-compatible directory
        """
        self.bids_dir = bids_dir
        self.out_dir = out_dir
        self.participant_label = participant_label
        self.queries = validate_queries(queries)
        self.work_dir = work_dir
        self.image_path = self.build_image_location(image_path)
        self.run_kwargs = self.arange_kwargs(run_kwargs)

    def build_image_location(self, image_path: str):
        if image_path is None:
            return Path(
                self.IMAGE_TEMPLATE.format(
                    image_location=self.DEFAULT_IMAGE_LOCATION,
                    version=self.__version__,
                )
            )
        else:
            return Path(image_path)

    def write_bids_filter_file(self):
        """
        Writes user and automatically defined BIDS filters to a json.
        """
        if self.work_dir is not None:
            bids_filter_path = Path(self.work_dir) / "bids_filter.json"
        else:
            bids_filter_path = Path("bids_filter.json").absolute()
        with open(str(bids_filter_path), "w") as fp:
            json.dump(self.queries, fp, indent=4)
            fp.close()
        self.run_kwargs["--bids-filter-file"] = str(bids_filter_path)
        return bids_filter_path

    def locate_freesurfer_license(self):
        if "--fs-license-file" not in self.run_kwargs:
            fs_license_path = locate_fs_license_file()
            if fs_license_path is not None:
                self.run_kwargs["--fs-license-file"] = str(fs_license_path)

    def get(self, name: str) -> Any:
        """
        An easy wrapper around *__getattribute__* to avoid errors upon missing attributes
        Parameters
        ----------
        name : str
            Attribute to get

        Returns
        -------
        Any
            Value of *name* attribute
        """
        if hasattr(self, name):
            return self.__getattribute__(name)
        return None

    def set_automatic_kwargs(self) -> dict:
        """

        Returns
        -------
        dict
            Aranges automatically defined kwargs into a suitable dictionary
        """
        run_kwargs = {}
        for key, attr in self.AUTOMATIC_KWARGS.items():
            value = self.get(attr)
            if value is not None:
                run_kwargs[key] = value
        return run_kwargs

    def arange_kwargs(self, user_kwargs: dict) -> dict:
        """
        Aranges both user and automatically defined kwargs into a suitable dictionary

        Parameters
        ----------
        user_kwargs : dict
            User-defined keyword arguments to be passed to *smriprep* command

        Returns
        -------
        dict
            Dictionary conatining both user-defined and *DmriprepManager*-defined keyword arguements to be passed to *smriprep*.
        """
        run_kwargs = {
            key: value for key, value in self.automatic_kwargs.items()
        }
        if user_kwargs is not None:
            for key, value in user_kwargs.items():
                run_kwargs[key] = value
        return run_kwargs

    def build_user_defined_command(self):
        """
        Builds the smriprep command via singularity
        """
        mounted_command, updated_kwargs = self.add_mounts_to_command()
        smriprep_command = self.COMMMAND_TEMPLATE.format(
            mounted_command=mounted_command, image_path=self.image_path
        )
        smriprep_command = self.add_kwargs_to_command(
            smriprep_command, updated_kwargs
        )
        return smriprep_command

    def add_mounts_to_command(self):
        mounted_command = self.COMMAND_MOUNT_TEMPLATE.format(
            bids_dir=self.bids_dir,
            out_dir=self.out_dir,
        )
        updated_kwargs = self.run_kwargs.copy()
        for kwarg, value in self.run_kwargs.items():
            stripped_kwarg = kwarg.strip("-")
            if stripped_kwarg in PATH_LIKE_KWARGS:
                target_value = stripped_kwarg.replace("-", "_")
                mounted_command += f" -B {value}:/{target_value}"
                updated_kwargs[kwarg] = f"/{target_value}"
        return mounted_command, updated_kwargs

    def add_kwargs_to_command(
        self, smriprep_command: str, updated_kwargs: dict
    ):
        for kwarg, value in updated_kwargs.items():
            if isinstance(value, bool):
                smriprep_command += f" {kwarg}"
            elif isinstance(value, list):
                for val in value:
                    smriprep_command += f" {val}"
            else:
                smriprep_command += f" {kwarg} {value}"
        return smriprep_command

    def build_command(self):
        bids_filter_path = self.write_bids_filter_file()
        self.locate_freesurfer_license()
        command = self.build_user_defined_command()
        return command, bids_filter_path

    def run(self):
        command, bids_filter_path = self.build_command()
        os.system(command)
        bids_filter_path.unlink()

    @property
    def automatic_kwargs(self) -> dict:
        return self.set_automatic_kwargs()
