"""
Connections configurations for *fmap_prep* pipelines.
"""

#: fieldmap preperation
INPUT_TO_MERGE_EDGES = [("fmap_ap", "in1"), ("fmap_pa", "in2")]
MERGE_TO_MRCAT_EDGES = [("out", "in_files")]
MRCAT_TO_OUTPUT_EDGES = [("out_file", "merged_phasediff")]
