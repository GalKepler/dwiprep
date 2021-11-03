import json
import os
from typing import Union, Any, Iterable
from pathlib import Path
from bids import BIDSLayout
from dwiprep.workflows.smri.utils.utils import (
    PATH_LIKE_KWARGS,
    DEFAULT_KWARGS,
    AUTOMATIC_KWARGS,
    FLAGS,
    OUTPUTS,
    locate_fs_license_file,
    validate_queries,
)


class SmriPrep(object):
    #: Version
    __version__ = "0.8.1"

    #: smriprep's singularity image pattern
    IMAGE_TEMPLATE = "{image_location}/smriprep:{version}.simg"

    #: Default location for singularity images
    DEFAULT_IMAGE_LOCATION = Path("/my_images")

    #: Kwargs that are predefined via the *dwiprep* initiation.
    AUTOMATIC_KWARGS = AUTOMATIC_KWARGS

    #: Command line template to format for execution.
    COMMAND_MOUNT_TEMPLATE = "singularity run --cleanenv -B {bids_dir}:/bids_dir -B {destination}:/destination"
    COMMMAND_TEMPLATE = (
        "{mounted_command} {image_path} /bids_dir /destination participant"
    )
    #: SmriPrep output pattern.
    SMRIPREP_OUTPUT_PATTERN: str = (
        "{main_dir}/**/{sub_dir}/sub-{subject_id}_{session_id}_{output_id}"
    )

    #: FreeSurfer output pattern.
    FS_OUTPUT_PATTERN: str = "{main_dir}/sub-{subject_id}/**/*{output_id}"

    #: Session results pattern.
    SESSION_PATTERN: str = "smriprep/sub-{subject_id}/ses-*"

    #: Expected outputs.
    OUTPUTS = OUTPUTS

    def __init__(
        self,
        bids_dir: Union[BIDSLayout, Path, str],
        destination: Union[Path, str],
        queries: dict,
        participant_label: str = None,
        image_path: str = None,
        run_kwargs: dict = DEFAULT_KWARGS,
        work_dir: Path = None,
    ):
        """
        Initiates an SmriPreo instance.

        Parameters
        ----------
        bids_dir : Union[Path, str]
            Either BIDSLayout or path-like object representing an existing BIDS-compatible dataset.
        destination : Union[Path, str]
            Path to smriprep's outputs
        queries : dict
            Dictionary describing specific localization of different entities in a BIDS-compatible directory
        """
        self.bids_dir = bids_dir
        self.destination = destination
        self.participant_label = participant_label
        self.queries = validate_queries(queries)
        self.work_dir = self.validate_working_directory(
            work_dir
            if work_dir is not None
            else Path(destination).parent / "work"
        )
        self.image_path = self.build_image_location(image_path)
        self.run_kwargs = self.arange_kwargs(run_kwargs)
        self.locate_freesurfer_license()

    def validate_working_directory(self, work_dir: Path):
        work_dir.mkdir(exist_ok=True)
        return work_dir

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
        bids_filter_path = self.work_dir / "bids_filter.json"
        with open(str(bids_filter_path), "w") as fp:
            json.dump(self.queries, fp, indent=4)
            fp.close()
        self.run_kwargs["bids-filter-file"] = str(bids_filter_path)
        return bids_filter_path

    def locate_freesurfer_license(self):
        if "fs-license-file" not in self.run_kwargs:
            fs_license_path = locate_fs_license_file()
            if fs_license_path is not None:
                self.run_kwargs["fs-license-file"] = str(fs_license_path)

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
        return smriprep_command + self.add_kwargs_to_command(updated_kwargs)

    def add_mounts_to_command(self):
        mounted_command = self.COMMAND_MOUNT_TEMPLATE.format(
            bids_dir=self.bids_dir,
            destination=self.destination,
        )
        updated_kwargs = self.run_kwargs.copy()
        for kwarg, value in self.run_kwargs.items():
            if kwarg in PATH_LIKE_KWARGS:
                target_value = kwarg.replace("-", "_")
                mounted_command += f" -B {value}:/{target_value}"
                updated_kwargs[kwarg] = f"/{target_value}"
        return mounted_command, updated_kwargs

    def add_kwargs_to_command(self, kwargs: dict):
        key_command = ""
        for key, value in kwargs.items():
            key_addition = f" --{key}"
            if isinstance(value, list):
                for val in value:
                    key_addition += f" {val}"
            elif key in FLAGS and value:
                pass
            else:
                key_addition += f" {value}"
            key_command += key_addition
        return key_command

    def build_command(self):
        bids_filter_path = self.write_bids_filter_file()
        command = self.build_user_defined_command()
        return command, bids_filter_path

    def run(self):
        command, bids_filter_path = self.build_command()
        os.system(command)
        bids_filter_path.unlink()

    def generate_fs_outputs(
        self, main_dir: str, subject_id: str, output_id: str
    ) -> Iterable[Path]:
        """
        Generate FreeSurfer output paths.

        Parameters
        ----------
        main_dir : str
            Main output directory
        output_id : str
            Output file name pattern

        Yields
        -------
        Path
            Output paths
        """
        pattern = self.FS_OUTPUT_PATTERN.format(
            main_dir=main_dir, subject_id=subject_id, output_id=output_id
        )
        return Path(self.destination).absolute().rglob(pattern)

    def generate_smriprep_outputs(
        self,
        main_dir: str,
        sub_dir: str,
        subject_id: str,
        session_id: str,
        output_id: str,
    ) -> Iterable[Path]:
        """
        Generate smriprep output paths.

        Parameters
        ----------
        main_dir : str
            Main output directory
        sub_dir : str
            Results sub-directory name
        subject_id : str
            String subject ID
        session_id : str
            String session ID
        output_id : str
            Output file name pattern

        Yields
        -------
        Path
            Output paths
        """
        pattern = self.SMRIPREP_OUTPUT_PATTERN.format(
            main_dir=main_dir,
            sub_dir=sub_dir,
            subject_id=subject_id,
            session_id=session_id,
            output_id=output_id,
        )

        return Path(self.destination).absolute().rglob(pattern)

    def find_output(
        self, partial_output: str, subject_id: str, session_id: str
    ):
        """
        uses the destination and some default dictionary to locate specific
        output files of *smriprep*.

        Parameters
        ----------
        partial_output : str
            A string that identifies a specific output
        subject_id : str
            Subject string ID
        session_id : str
            Session string ID
        """
        main_dir, sub_dir, output_id = self.OUTPUTS.get(partial_output)
        if main_dir == "freesurfer":
            outputs = list(
                self.generate_fs_outputs(main_dir, subject_id, output_id)
            )
        elif main_dir == "smriprep":
            outputs = list(
                self.generate_smriprep_outputs(
                    main_dir, sub_dir, subject_id, session_id, output_id
                )
            )
        # if len(outputs) == 1:
        #     return str(outputs[0])
        # elif len(outputs) > 1:
        if ("native" in partial_output) and (
            "transform" not in partial_output
        ):
            return [str(f) for f in outputs if ("MNI" not in f.name)]
        return [str(f) for f in outputs]

    def generate_output_dict(self) -> dict:
        """
        Generates a dictionary of the expected output file paths by key.

        Returns
        -------
        dict
            Output files by key
        """
        output_dict = {}
        subject_ids = self.run_kwargs.get("participant_label")
        subject_ids = (
            subject_ids if isinstance(subject_ids, list) else [subject_ids]
        )
        for subject_id in subject_ids:
            output_dict[subject_id] = {}
            # session_pattern = self.SESSION_PATTERN.format(
            #     subject_id=subject_id
            # )
            for key in self.OUTPUTS:
                output_dict[subject_id][key] = self.find_output(
                    key, subject_id, "*"
                )
        if len(output_dict) == 1:
            return output_dict.get(subject_id)
        return output_dict

    @property
    def automatic_kwargs(self) -> dict:
        return self.set_automatic_kwargs()
