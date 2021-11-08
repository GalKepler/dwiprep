from collections import defaultdict
from json import dumps, loads
from pathlib import Path
from pkg_resources import resource_filename as _pkgres
import re
import nibabel as nb

from nipype.interfaces.base import SimpleInterface, traits
from nipype.interfaces.base import (
    traits,
    isdefined,
    TraitedSpec,
    BaseInterfaceInputSpec,
    DynamicTraitedSpec,
    File,
    InputMultiObject,
    OutputMultiObject,
    Str,
    SimpleInterface,
)
from nipype.interfaces.io import add_traits
from niworkflows.utils.bids import relative_to_root
from niworkflows.utils.misc import splitext as _splitext, _copy_any
from niworkflows.utils.images import (
    set_consumables,
    unsafe_write_nifti_header_and_data,
)
from templateflow.api import templates as _get_template_list

regz = re.compile(r"\.gz$")

_pybids_spec = loads(
    Path(_pkgres("dwiprep", "data/bids_specifications.json")).read_text()
)
BIDS_DERIV_ENTITIES = frozenset({e["name"] for e in _pybids_spec["entities"]})
BIDS_DERIV_PATTERNS = tuple(_pybids_spec["default_path_patterns"])
STANDARD_SPACES = _get_template_list()


def _none():
    return None


# Automatically coerce certain suffixes (DerivativesDataSink)
DEFAULT_DTYPES = defaultdict(
    _none,
    (
        ("mask", "uint8"),
        ("dseg", "int16"),
        ("probseg", "float32"),
        ("boldref", "source"),
    ),
)


class _DerivativesDataSinkInputSpec(
    DynamicTraitedSpec, BaseInterfaceInputSpec
):
    base_directory = traits.Directory(
        desc="Path to the base directory for storing data."
    )
    check_hdr = traits.Bool(
        True, usedefault=True, desc="fix headers of NIfTI outputs"
    )
    compress = InputMultiObject(
        traits.Either(None, traits.Bool),
        usedefault=True,
        desc="whether ``in_file`` should be compressed (True), uncompressed (False) "
        "or left unmodified (None, default).",
    )
    data_dtype = Str(
        desc="NumPy datatype to coerce NIfTI data to, or `source` to"
        "match the input file dtype"
    )
    dismiss_entities = InputMultiObject(
        traits.Either(None, Str),
        usedefault=True,
        desc="a list entities that will not be propagated from the source file",
    )
    in_file = InputMultiObject(
        File(exists=True), mandatory=True, desc="the object to be saved"
    )
    meta_dict = traits.DictStrAny(
        desc="an input dictionary containing metadata"
    )
    source_file = InputMultiObject(
        File(exists=False),
        mandatory=True,
        desc="the source file(s) to extract entities from",
    )


class _DerivativesDataSinkOutputSpec(TraitedSpec):
    out_file = OutputMultiObject(File(exists=True, desc="written file path"))
    out_meta = OutputMultiObject(
        File(exists=True, desc="written JSON sidecar path")
    )
    compression = OutputMultiObject(
        traits.Either(None, traits.Bool),
        desc="whether ``in_file`` should be compressed (True), uncompressed (False) "
        "or left unmodified (None).",
    )
    fixed_hdr = traits.List(
        traits.Bool, desc="whether derivative header was fixed"
    )


class DerivativesDataSink(SimpleInterface):
    """
    Store derivative files.

    Saves the ``in_file`` into a BIDS-Derivatives folder provided
    by ``base_directory``, given the input reference ``source_file``.

    >>> import tempfile
    >>> tmpdir = Path(tempfile.mkdtemp())
    >>> tmpfile = tmpdir / 'a_temp_file.nii.gz'
    >>> tmpfile.open('w').close()  # "touch" the file
    >>> t1w_source = bids_collect_data(
    ...     str(datadir / 'ds114'), '01', bids_validate=False)[0]['t1w'][0]
    >>> dsink = DerivativesDataSink(base_directory=str(tmpdir), check_hdr=False)
    >>> dsink.inputs.in_file = str(tmpfile)
    >>> dsink.inputs.source_file = t1w_source
    >>> dsink.inputs.desc = 'denoised'
    >>> dsink.inputs.compress = False
    >>> res = dsink.run()
    >>> res.outputs.out_file  # doctest: +ELLIPSIS
    '.../niworkflows/sub-01/ses-retest/anat/sub-01_ses-retest_desc-denoised_T1w.nii'

    >>> tmpfile = tmpdir / 'a_temp_file.nii'
    >>> tmpfile.open('w').close()  # "touch" the file
    >>> dsink = DerivativesDataSink(base_directory=str(tmpdir), check_hdr=False,
    ...                             allowed_entities=("custom",))
    >>> dsink.inputs.in_file = str(tmpfile)
    >>> dsink.inputs.source_file = t1w_source
    >>> dsink.inputs.custom = 'noise'
    >>> res = dsink.run()
    >>> res.outputs.out_file  # doctest: +ELLIPSIS
    '.../niworkflows/sub-01/ses-retest/anat/sub-01_ses-retest_custom-noise_T1w.nii'

    >>> dsink = DerivativesDataSink(base_directory=str(tmpdir), check_hdr=False,
    ...                             allowed_entities=("custom",))
    >>> dsink.inputs.in_file = [str(tmpfile), str(tmpfile)]
    >>> dsink.inputs.source_file = t1w_source
    >>> dsink.inputs.custom = [1, 2]
    >>> dsink.inputs.compress = True
    >>> res = dsink.run()
    >>> res.outputs.out_file  # doctest: +ELLIPSIS
    ['.../niworkflows/sub-01/ses-retest/anat/sub-01_ses-retest_custom-1_T1w.nii.gz',
     '.../niworkflows/sub-01/ses-retest/anat/sub-01_ses-retest_custom-2_T1w.nii.gz']

    >>> dsink = DerivativesDataSink(base_directory=str(tmpdir), check_hdr=False,
    ...                             allowed_entities=("custom1", "custom2"))
    >>> dsink.inputs.in_file = [str(tmpfile)] * 2
    >>> dsink.inputs.source_file = t1w_source
    >>> dsink.inputs.custom1 = [1, 2]
    >>> dsink.inputs.custom2 = "b"
    >>> res = dsink.run()
    >>> res.outputs.out_file  # doctest: +ELLIPSIS
    ['.../niworkflows/sub-01/ses-retest/anat/sub-01_ses-retest_custom1-1_custom2-b_T1w.nii',
     '.../niworkflows/sub-01/ses-retest/anat/sub-01_ses-retest_custom1-2_custom2-b_T1w.nii']

    When multiple source files are passed, only common entities are passed down.
    For example, if two T1w images from different sessions are used to generate
    a single image, the session entity is removed automatically.

    >>> bids_dir = tmpdir / 'bidsroot'
    >>> multi_source = [
    ...     bids_dir / 'sub-02/ses-A/anat/sub-02_ses-A_T1w.nii.gz',
    ...     bids_dir / 'sub-02/ses-B/anat/sub-02_ses-B_T1w.nii.gz']
    >>> for source_file in multi_source:
    ...     source_file.parent.mkdir(parents=True, exist_ok=True)
    ...     _ = source_file.write_text("")
    >>> dsink = DerivativesDataSink(base_directory=str(tmpdir), check_hdr=False)
    >>> dsink.inputs.in_file = str(tmpfile)
    >>> dsink.inputs.source_file = list(map(str, multi_source))
    >>> dsink.inputs.desc = 'preproc'
    >>> res = dsink.run()
    >>> res.outputs.out_file  # doctest: +ELLIPSIS
    '.../niworkflows/sub-02/anat/sub-02_desc-preproc_T1w.nii'

    If, on the other hand, only one is used, the session is preserved:

    >>> dsink.inputs.source_file = str(multi_source[0])
    >>> res = dsink.run()
    >>> res.outputs.out_file  # doctest: +ELLIPSIS
    '.../niworkflows/sub-02/ses-A/anat/sub-02_ses-A_desc-preproc_T1w.nii'

    >>> bids_dir = tmpdir / 'bidsroot' / 'sub-02' / 'ses-noanat' / 'func'
    >>> bids_dir.mkdir(parents=True, exist_ok=True)
    >>> tricky_source = bids_dir / 'sub-02_ses-noanat_task-rest_run-01_bold.nii.gz'
    >>> tricky_source.open('w').close()
    >>> dsink = DerivativesDataSink(base_directory=str(tmpdir), check_hdr=False)
    >>> dsink.inputs.in_file = str(tmpfile)
    >>> dsink.inputs.source_file = str(tricky_source)
    >>> dsink.inputs.desc = 'preproc'
    >>> res = dsink.run()
    >>> res.outputs.out_file  # doctest: +ELLIPSIS
    '.../niworkflows/sub-02/ses-noanat/func/sub-02_ses-noanat_task-rest_run-1_\
desc-preproc_bold.nii'

    >>> bids_dir = tmpdir / 'bidsroot' / 'sub-02' / 'ses-noanat' / 'func'
    >>> bids_dir.mkdir(parents=True, exist_ok=True)
    >>> tricky_source = bids_dir / 'sub-02_ses-noanat_task-rest_run-1_bold.nii.gz'
    >>> tricky_source.open('w').close()
    >>> dsink = DerivativesDataSink(base_directory=str(tmpdir), check_hdr=False)
    >>> dsink.inputs.in_file = str(tmpfile)
    >>> dsink.inputs.source_file = str(tricky_source)
    >>> dsink.inputs.desc = 'preproc'
    >>> dsink.inputs.RepetitionTime = 0.75
    >>> res = dsink.run()
    >>> res.outputs.out_meta  # doctest: +ELLIPSIS
    '.../niworkflows/sub-02/ses-noanat/func/sub-02_ses-noanat_task-rest_run-1_\
desc-preproc_bold.json'

    >>> Path(res.outputs.out_meta).read_text().splitlines()[1]
    '  "RepetitionTime": 0.75'

    >>> bids_dir = tmpdir / 'bidsroot' / 'sub-02' / 'ses-noanat' / 'func'
    >>> bids_dir.mkdir(parents=True, exist_ok=True)
    >>> tricky_source = bids_dir / 'sub-02_ses-noanat_task-rest_run-01_bold.nii.gz'
    >>> tricky_source.open('w').close()
    >>> dsink = DerivativesDataSink(base_directory=str(tmpdir), check_hdr=False,
    ...                             SkullStripped=True)
    >>> dsink.inputs.in_file = str(tmpfile)
    >>> dsink.inputs.source_file = str(tricky_source)
    >>> dsink.inputs.desc = 'preproc'
    >>> dsink.inputs.space = 'MNI152NLin6Asym'
    >>> dsink.inputs.resolution = '01'
    >>> dsink.inputs.RepetitionTime = 0.75
    >>> res = dsink.run()
    >>> res.outputs.out_meta  # doctest: +ELLIPSIS
    '.../niworkflows/sub-02/ses-noanat/func/sub-02_ses-noanat_task-rest_run-1_\
space-MNI152NLin6Asym_res-01_desc-preproc_bold.json'

    >>> lines = Path(res.outputs.out_meta).read_text().splitlines()
    >>> lines[1]
    '  "RepetitionTime": 0.75,'

    >>> lines[2]
    '  "SkullStripped": true'

    >>> bids_dir = tmpdir / 'bidsroot' / 'sub-02' / 'ses-noanat' / 'func'
    >>> bids_dir.mkdir(parents=True, exist_ok=True)
    >>> tricky_source = bids_dir / 'sub-02_ses-noanat_task-rest_run-01_bold.nii.gz'
    >>> tricky_source.open('w').close()
    >>> dsink = DerivativesDataSink(base_directory=str(tmpdir), check_hdr=False,
    ...                             SkullStripped=True)
    >>> dsink.inputs.in_file = str(tmpfile)
    >>> dsink.inputs.source_file = str(tricky_source)
    >>> dsink.inputs.desc = 'preproc'
    >>> dsink.inputs.resolution = 'native'
    >>> dsink.inputs.space = 'MNI152NLin6Asym'
    >>> dsink.inputs.RepetitionTime = 0.75
    >>> dsink.inputs.meta_dict = {'RepetitionTime': 1.75, 'SkullStripped': False, 'Z': 'val'}
    >>> res = dsink.run()
    >>> res.outputs.out_meta  # doctest: +ELLIPSIS
    '.../niworkflows/sub-02/ses-noanat/func/sub-02_ses-noanat_task-rest_run-1_\
space-MNI152NLin6Asym_desc-preproc_bold.json'

    >>> lines = Path(res.outputs.out_meta).read_text().splitlines()
    >>> lines[1]
    '  "RepetitionTime": 0.75,'

    >>> lines[2]
    '  "SkullStripped": true,'

    >>> lines[3]
    '  "Z": "val"'

    """

    input_spec = _DerivativesDataSinkInputSpec
    output_spec = _DerivativesDataSinkOutputSpec
    out_path_base = "niworkflows"
    _always_run = True
    _allowed_entities = set(BIDS_DERIV_ENTITIES)

    def __init__(self, allowed_entities=None, out_path_base=None, **inputs):
        """Initialize the SimpleInterface and extend inputs with custom entities."""
        self._allowed_entities = set(allowed_entities or []).union(
            self._allowed_entities
        )
        if out_path_base:
            self.out_path_base = out_path_base

        self._metadata = {}
        self._static_traits = self.input_spec.class_editable_traits() + sorted(
            self._allowed_entities
        )
        for dynamic_input in set(inputs) - set(self._static_traits):
            self._metadata[dynamic_input] = inputs.pop(dynamic_input)

        # First regular initialization (constructs InputSpec object)
        super().__init__(**inputs)
        add_traits(self.inputs, self._allowed_entities)
        for k in self._allowed_entities.intersection(list(inputs.keys())):
            # Add additional input fields (self.inputs is an object)
            setattr(self.inputs, k, inputs[k])

    def _run_interface(self, runtime):
        from bids.layout import parse_file_entities
        from bids.layout.writing import build_path
        from bids.utils import listify

        # Ready the output folder
        base_directory = runtime.cwd
        if isdefined(self.inputs.base_directory):
            base_directory = self.inputs.base_directory
        base_directory = Path(base_directory).absolute()
        out_path = base_directory / self.out_path_base
        out_path.mkdir(exist_ok=True, parents=True)

        # Ensure we have a list
        in_file = listify(self.inputs.in_file)

        # Read in the dictionary of metadata
        if isdefined(self.inputs.meta_dict):
            meta = self.inputs.meta_dict
            # inputs passed in construction take priority
            meta.update(self._metadata)
            self._metadata = meta

        # Initialize entities with those from the source file.
        in_entities = [
            parse_file_entities(str(relative_to_root(source_file)))
            for source_file in self.inputs.source_file
        ]
        out_entities = {
            k: v
            for k, v in in_entities[0].items()
            if all(ent.get(k) == v for ent in in_entities[1:])
        }
        for drop_entity in listify(self.inputs.dismiss_entities or []):
            out_entities.pop(drop_entity, None)

        # Override extension with that of the input file(s)
        out_entities["extension"] = [
            # _splitext does not accept .surf.gii (for instance)
            "".join(Path(orig_file).suffixes).lstrip(".")
            for orig_file in in_file
        ]

        compress = listify(self.inputs.compress) or [None]
        if len(compress) == 1:
            compress = compress * len(in_file)
        for i, ext in enumerate(out_entities["extension"]):
            if compress[i] is not None:
                ext = regz.sub("", ext)
                out_entities["extension"][i] = (
                    f"{ext}.gz" if compress[i] else ext
                )

        # Override entities with those set as inputs
        for key in self._allowed_entities:
            value = getattr(self.inputs, key)
            if value is not None and isdefined(value):
                out_entities[key] = value

        # Clean up native resolution with space
        if out_entities.get("resolution") == "native" and out_entities.get(
            "space"
        ):
            out_entities.pop("resolution", None)

        if len(set(out_entities["extension"])) == 1:
            out_entities["extension"] = out_entities["extension"][0]

        # Insert custom (non-BIDS) entities from allowed_entities.
        custom_entities = set(out_entities.keys()) - set(BIDS_DERIV_ENTITIES)
        patterns = BIDS_DERIV_PATTERNS
        if custom_entities:
            # Example: f"{key}-{{{key}}}" -> "task-{task}"
            custom_pat = "_".join(
                f"{key}-{{{key}}}" for key in sorted(custom_entities)
            )
            patterns = [
                pat.replace("_{suffix", "_".join(("", custom_pat, "{suffix")))
                for pat in patterns
            ]

        # Prepare SimpleInterface outputs object
        self._results["out_file"] = []
        self._results["compression"] = []
        self._results["fixed_hdr"] = [False] * len(in_file)

        dest_files = build_path(out_entities, path_patterns=patterns)
        if not dest_files:
            raise ValueError(
                f"Could not build path with entities {out_entities}."
            )

        # Make sure the interpolated values is embedded in a list, and check
        dest_files = listify(dest_files)
        if len(in_file) != len(dest_files):
            raise ValueError(
                f"Input files ({len(in_file)}) not matched "
                f"by interpolated patterns ({len(dest_files)})."
            )

        for i, (orig_file, dest_file) in enumerate(zip(in_file, dest_files)):
            out_file = out_path / dest_file
            out_file.parent.mkdir(exist_ok=True, parents=True)
            self._results["out_file"].append(str(out_file))
            self._results["compression"].append(str(dest_file).endswith(".gz"))

            # Set data and header iff changes need to be made. If these are
            # still None when it's time to write, just copy.
            new_data, new_header = None, None

            is_nifti = out_file.name.endswith(
                (".nii", ".nii.gz")
            ) and not out_file.name.endswith(
                (".dtseries.nii", ".dtseries.nii.gz")
            )
            data_dtype = (
                self.inputs.data_dtype or DEFAULT_DTYPES[self.inputs.suffix]
            )
            if is_nifti and any((self.inputs.check_hdr, data_dtype)):
                nii = nb.load(orig_file)

                if self.inputs.check_hdr:
                    hdr = nii.header
                    curr_units = tuple(
                        [
                            None if u == "unknown" else u
                            for u in hdr.get_xyzt_units()
                        ]
                    )
                    curr_codes = (
                        int(hdr["qform_code"]),
                        int(hdr["sform_code"]),
                    )

                    # Default to mm, use sec if data type is bold
                    units = (
                        curr_units[0] or "mm",
                        "sec" if out_entities["suffix"] == "bold" else None,
                    )
                    xcodes = (1, 1)  # Derivative in its original scanner space
                    if self.inputs.space:
                        xcodes = (
                            (4, 4)
                            if self.inputs.space in STANDARD_SPACES
                            else (2, 2)
                        )

                    if curr_codes != xcodes or curr_units != units:
                        self._results["fixed_hdr"][i] = True
                        new_header = hdr.copy()
                        new_header.set_qform(nii.affine, xcodes[0])
                        new_header.set_sform(nii.affine, xcodes[1])
                        new_header.set_xyzt_units(*units)

                if data_dtype == "source":  # match source dtype
                    try:
                        data_dtype = nb.load(
                            self.inputs.source_file[0]
                        ).get_data_dtype()
                    except Exception:
                        LOGGER.warning(
                            f"Could not get data type of file {self.inputs.source_file[0]}"
                        )
                        data_dtype = None

                if data_dtype:
                    data_dtype = np.dtype(data_dtype)
                    orig_dtype = nii.get_data_dtype()
                    if orig_dtype != data_dtype:
                        LOGGER.warning(
                            f"Changing {out_file} dtype from {orig_dtype} to {data_dtype}"
                        )
                        # coerce dataobj to new data dtype
                        if np.issubdtype(data_dtype, np.integer):
                            new_data = np.rint(nii.dataobj).astype(data_dtype)
                        else:
                            new_data = np.asanyarray(
                                nii.dataobj, dtype=data_dtype
                            )
                        # and set header to match
                        if new_header is None:
                            new_header = nii.header.copy()
                        new_header.set_data_dtype(data_dtype)
                del nii

            if new_data is new_header is None:
                _copy_any(orig_file, str(out_file))
            else:
                orig_img = nb.load(orig_file)
                if new_data is None:
                    set_consumables(new_header, orig_img.dataobj)
                    new_data = orig_img.dataobj.get_unscaled()
                else:
                    # Without this, we would be writing nans
                    # This is our punishment for hacking around nibabel defaults
                    new_header.set_slope_inter(slope=1.0, inter=0.0)
                unsafe_write_nifti_header_and_data(
                    fname=out_file, header=new_header, data=new_data
                )
                del orig_img

        if len(self._results["out_file"]) == 1:
            meta_fields = self.inputs.copyable_trait_names()
            self._metadata.update(
                {
                    k: getattr(self.inputs, k)
                    for k in meta_fields
                    if k not in self._static_traits
                }
            )
            if self._metadata:
                out_file = Path(self._results["out_file"][0])
                # 1.3.x hack
                # For dtseries, we have been generating weird non-BIDS JSON files.
                # We can safely keep producing them to avoid breaking derivatives, but
                # only the existing keys should keep going into them.
                if out_file.name.endswith(".dtseries.nii"):
                    legacy_metadata = {}
                    for key in (
                        "grayordinates",
                        "space",
                        "surface",
                        "surface_density",
                        "volume",
                    ):
                        if key in self._metadata:
                            legacy_metadata[key] = self._metadata.pop(key)
                    if legacy_metadata:
                        sidecar = (
                            out_file.parent
                            / f"{_splitext(str(out_file))[0]}.json"
                        )
                        sidecar.write_text(
                            dumps(legacy_metadata, sort_keys=True, indent=2)
                        )
                # The future: the extension is the first . and everything after
                sidecar = (
                    out_file.parent / f"{out_file.name.split('.', 1)[0]}.json"
                )
                sidecar.write_text(
                    dumps(self._metadata, sort_keys=True, indent=2)
                )
                self._results["out_meta"] = str(sidecar)
        return runtime
