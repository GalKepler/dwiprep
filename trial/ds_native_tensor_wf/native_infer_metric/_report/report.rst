Node: ds_native_tensor_wf (native_infer_metric (utility)
========================================================


 Hierarchy : trial.ds_native_tensor_wf.native_infer_metric
 Exec ID : native_infer_metric


Original Inputs
---------------


* function_str : def infer_metric(in_file: str) -> str:
    """
    A simple function to infer tensor-derived metric from file's name.

    Parameters
    ----------
    in_file : str
        A string representing an existing file.

    Returns
    -------
    str
        A metric identifier/label for BIDS specification (i.e, fa, adc, rd etc.)
    """
    from pathlib import Path

    file_name = Path(in_file).name
    return file_name.split(".")[0].lower(), in_file

* in_file : ['/media/groot/Yalla/media/MRI/work/single_subject_242_wf/dwi_preproc_ses_202104251808_dir_ap_wf/tensor_estimation_wf/tensor2metric/fa.nii.gz', '/media/groot/Yalla/media/MRI/work/single_subject_242_wf/dwi_preproc_ses_202104251808_dir_ap_wf/tensor_estimation_wf/tensor2metric/adc.nii.gz', '/media/groot/Yalla/media/MRI/work/single_subject_242_wf/dwi_preproc_ses_202104251808_dir_ap_wf/tensor_estimation_wf/tensor2metric/ad.nii.gz', '/media/groot/Yalla/media/MRI/work/single_subject_242_wf/dwi_preproc_ses_202104251808_dir_ap_wf/tensor_estimation_wf/tensor2metric/rd.nii.gz', '/media/groot/Yalla/media/MRI/work/single_subject_242_wf/dwi_preproc_ses_202104251808_dir_ap_wf/tensor_estimation_wf/tensor2metric/cl.nii.gz', '/media/groot/Yalla/media/MRI/work/single_subject_242_wf/dwi_preproc_ses_202104251808_dir_ap_wf/tensor_estimation_wf/tensor2metric/cp.nii.gz', '/media/groot/Yalla/media/MRI/work/single_subject_242_wf/dwi_preproc_ses_202104251808_dir_ap_wf/tensor_estimation_wf/tensor2metric/cs.nii.gz', '/media/groot/Yalla/media/MRI/work/single_subject_242_wf/dwi_preproc_ses_202104251808_dir_ap_wf/tensor_estimation_wf/tensor2metric/evec.nii.gz', '/media/groot/Yalla/media/MRI/work/single_subject_242_wf/dwi_preproc_ses_202104251808_dir_ap_wf/tensor_estimation_wf/tensor2metric/eval.nii.gz']


Execution Inputs
----------------


* function_str : def infer_metric(in_file: str) -> str:
    """
    A simple function to infer tensor-derived metric from file's name.

    Parameters
    ----------
    in_file : str
        A string representing an existing file.

    Returns
    -------
    str
        A metric identifier/label for BIDS specification (i.e, fa, adc, rd etc.)
    """
    from pathlib import Path

    file_name = Path(in_file).name
    return file_name.split(".")[0].lower(), in_file

* in_file : ['/media/groot/Yalla/media/MRI/work/single_subject_242_wf/dwi_preproc_ses_202104251808_dir_ap_wf/tensor_estimation_wf/tensor2metric/fa.nii.gz', '/media/groot/Yalla/media/MRI/work/single_subject_242_wf/dwi_preproc_ses_202104251808_dir_ap_wf/tensor_estimation_wf/tensor2metric/adc.nii.gz', '/media/groot/Yalla/media/MRI/work/single_subject_242_wf/dwi_preproc_ses_202104251808_dir_ap_wf/tensor_estimation_wf/tensor2metric/ad.nii.gz', '/media/groot/Yalla/media/MRI/work/single_subject_242_wf/dwi_preproc_ses_202104251808_dir_ap_wf/tensor_estimation_wf/tensor2metric/rd.nii.gz', '/media/groot/Yalla/media/MRI/work/single_subject_242_wf/dwi_preproc_ses_202104251808_dir_ap_wf/tensor_estimation_wf/tensor2metric/cl.nii.gz', '/media/groot/Yalla/media/MRI/work/single_subject_242_wf/dwi_preproc_ses_202104251808_dir_ap_wf/tensor_estimation_wf/tensor2metric/cp.nii.gz', '/media/groot/Yalla/media/MRI/work/single_subject_242_wf/dwi_preproc_ses_202104251808_dir_ap_wf/tensor_estimation_wf/tensor2metric/cs.nii.gz', '/media/groot/Yalla/media/MRI/work/single_subject_242_wf/dwi_preproc_ses_202104251808_dir_ap_wf/tensor_estimation_wf/tensor2metric/evec.nii.gz', '/media/groot/Yalla/media/MRI/work/single_subject_242_wf/dwi_preproc_ses_202104251808_dir_ap_wf/tensor_estimation_wf/tensor2metric/eval.nii.gz']


Execution Outputs
-----------------


* in_file : ['/media/groot/Yalla/media/MRI/work/single_subject_242_wf/dwi_preproc_ses_202104251808_dir_ap_wf/tensor_estimation_wf/tensor2metric/fa.nii.gz', '/media/groot/Yalla/media/MRI/work/single_subject_242_wf/dwi_preproc_ses_202104251808_dir_ap_wf/tensor_estimation_wf/tensor2metric/adc.nii.gz', '/media/groot/Yalla/media/MRI/work/single_subject_242_wf/dwi_preproc_ses_202104251808_dir_ap_wf/tensor_estimation_wf/tensor2metric/ad.nii.gz', '/media/groot/Yalla/media/MRI/work/single_subject_242_wf/dwi_preproc_ses_202104251808_dir_ap_wf/tensor_estimation_wf/tensor2metric/rd.nii.gz', '/media/groot/Yalla/media/MRI/work/single_subject_242_wf/dwi_preproc_ses_202104251808_dir_ap_wf/tensor_estimation_wf/tensor2metric/cl.nii.gz', '/media/groot/Yalla/media/MRI/work/single_subject_242_wf/dwi_preproc_ses_202104251808_dir_ap_wf/tensor_estimation_wf/tensor2metric/cp.nii.gz', '/media/groot/Yalla/media/MRI/work/single_subject_242_wf/dwi_preproc_ses_202104251808_dir_ap_wf/tensor_estimation_wf/tensor2metric/cs.nii.gz', '/media/groot/Yalla/media/MRI/work/single_subject_242_wf/dwi_preproc_ses_202104251808_dir_ap_wf/tensor_estimation_wf/tensor2metric/evec.nii.gz', '/media/groot/Yalla/media/MRI/work/single_subject_242_wf/dwi_preproc_ses_202104251808_dir_ap_wf/tensor_estimation_wf/tensor2metric/eval.nii.gz']
* metric : ['fa', 'adc', 'ad', 'rd', 'cl', 'cp', 'cs', 'evec', 'eval']


Subnode reports
---------------


 subnode 0 : /home/groot/Projects/dwiprep/trial/ds_native_tensor_wf/native_infer_metric/mapflow/_native_infer_metric0/_report/report.rst
 subnode 1 : /home/groot/Projects/dwiprep/trial/ds_native_tensor_wf/native_infer_metric/mapflow/_native_infer_metric1/_report/report.rst
 subnode 2 : /home/groot/Projects/dwiprep/trial/ds_native_tensor_wf/native_infer_metric/mapflow/_native_infer_metric2/_report/report.rst
 subnode 3 : /home/groot/Projects/dwiprep/trial/ds_native_tensor_wf/native_infer_metric/mapflow/_native_infer_metric3/_report/report.rst
 subnode 4 : /home/groot/Projects/dwiprep/trial/ds_native_tensor_wf/native_infer_metric/mapflow/_native_infer_metric4/_report/report.rst
 subnode 5 : /home/groot/Projects/dwiprep/trial/ds_native_tensor_wf/native_infer_metric/mapflow/_native_infer_metric5/_report/report.rst
 subnode 6 : /home/groot/Projects/dwiprep/trial/ds_native_tensor_wf/native_infer_metric/mapflow/_native_infer_metric6/_report/report.rst
 subnode 7 : /home/groot/Projects/dwiprep/trial/ds_native_tensor_wf/native_infer_metric/mapflow/_native_infer_metric7/_report/report.rst
 subnode 8 : /home/groot/Projects/dwiprep/trial/ds_native_tensor_wf/native_infer_metric/mapflow/_native_infer_metric8/_report/report.rst

