MANDATORY_ENTITIES = ["dwi"]

RECOMMENDED_ENTITIES = ["fmap"]

RELEVANT_DATA_TYPES = ["dwi", "fmap"]

WORK_DIR_NAME = "dmriprep_wf"

OUTPUT_ENTITIES = {"raw_mif": {"desc": "orig"}}

OUTPUT_PATTERNS = "sub-{subject}/[ses-{session}/][{datatype}/]sub-{subject}[_ses-{session}][_acq-{acquisition}][_dir-{direction}][_desc-{desc}]_{suffix}.nii.gz"
