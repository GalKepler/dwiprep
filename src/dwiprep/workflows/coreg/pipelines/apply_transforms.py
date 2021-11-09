import nipype.pipeline.engine as pe
import nipype.interfaces.utility as niu


def init_apply_transforms_wf(input_fields: list, name="apply_transforms"):
    wf = pe.Workflow(name=name)
    input_fields += ["dwi_file", "epi_ref_file", "itk_epi_to_t1w"]
    inputnode = pe.Node(niu.IdentityInterface(fields=input_fields))
    outputnode = pe.Node(niu.IdentityInterface(fields=input_fields))
    # for field in input_fields:
    # apply_transform =
