import nipype.pipeline.engine as pe
import nipype.interfaces.mrtrix3 as mrt
import nipype.interfaces.utility as niu
import subprocess

DWIFSLPREPROC_KWARGS = {
    "rpe_options": "pair",
    "align_seepi": True,
    "eddy_options": " --slm=linear",
}


def infer_phase_encoding_direction_mif(in_file: str) -> str:
    """
    Utilizes *mrinfo* for a specific query of phase encoding direction.

    Parameters
    ----------
    in_file : str
        File to query

    Returns
    -------
    str
        Phase Encoding Direction as denoted in *in_file*`s header.
    """
    import subprocess

    return (
        subprocess.check_output(
            ["mrinfo", str(in_file), "-property", "PhaseEncodingDirection"]
        )
        .decode("utf-8")
        .replace("\n", "")
    )


def init_preprocess_wf(name="preprocess_wf"):
    wf = pe.Workflow(name=name)
    inputnode = pe.Node(
        niu.IdentityInterface(fields=["dwi_file", "merged_phasediff"]),
        name="inputnode",
    )
    outputnode = pe.Node(
        niu.IdentityInterface(fields=["dwi_preproc"]), name="outputnode"
    )

    dwidenoise = pe.Node(mrt.DWIDenoise(), name="denoise")
    infer_pe = pe.Node(
        niu.Function(
            input_names=["in_file"],
            output_names=["pe_dir"],
            function=infer_phase_encoding_direction_mif,
        ),
        name="infer_pe",
    )
    dwipreproc = pe.Node(
        mrt.DWIPreproc(**DWIFSLPREPROC_KWARGS), name="dwipreproc"
    )
    biascorrect = pe.Node(
        mrt.DWIBiasCorrect(use_ants=True), name="biascorrect"
    )
    wf.connect(
        [
            (inputnode, dwidenoise, [("dwi_file", "in_file")]),
            (
                inputnode,
                dwipreproc,
                [("merged_phasediff", "in_epi")],
            ),
            (dwidenoise, infer_pe, [("out_file", "in_file")]),
            (dwidenoise, dwipreproc, [("out_file", "in_file")]),
            (infer_pe, dwipreproc, [("pe_dir", "pe_dir")]),
            (dwipreproc, biascorrect, [("out_file", "in_file")]),
            (biascorrect, outputnode, [("out_file", "dwi_preproc")]),
        ]
    )
    return wf
