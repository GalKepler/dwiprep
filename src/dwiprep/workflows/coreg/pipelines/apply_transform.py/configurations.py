"""
Configurations for *fmap_prep* pipeline.
"""
#: i/o
INPUT_NODE_FIELDS = ["fmap_ap", "fmap_pa"]
OUTPUT_NODE_FIELDS = ["merged_phasediff"]

#: Keyword arguments
MERGE_KWARGS = dict(numinputs=2)
MRCAT_KWARGS = dict(axis=3)
