Node: ds_native_tensor_wf (ds_native_tensor (dds)
=================================================


 Hierarchy : trial.ds_native_tensor_wf.ds_native_tensor
 Exec ID : ds_native_tensor


Original Inputs
---------------


* acquisition : <undefined>
* atlas : <undefined>
* base_directory : <undefined>
* ceagent : <undefined>
* check_hdr : True
* cohort : <undefined>
* compress : [True]
* data_dtype : <undefined>
* datatype : tensor
* density : <undefined>
* desc : <undefined>
* direction : <undefined>
* dismiss_entities : <undefined>
* echo : <undefined>
* extension : <undefined>
* fmap : <undefined>
* fmapid : <undefined>
* from : <undefined>
* hemi : <undefined>
* in_file : [['/media/groot/Yalla/media/MRI/work/single_subject_242_wf/dwi_preproc_ses_202104251808_dir_ap_wf/tensor_estimation_wf/tensor2metric/fa.nii.gz'], ['/media/groot/Yalla/media/MRI/work/single_subject_242_wf/dwi_preproc_ses_202104251808_dir_ap_wf/tensor_estimation_wf/tensor2metric/adc.nii.gz'], ['/media/groot/Yalla/media/MRI/work/single_subject_242_wf/dwi_preproc_ses_202104251808_dir_ap_wf/tensor_estimation_wf/tensor2metric/ad.nii.gz'], ['/media/groot/Yalla/media/MRI/work/single_subject_242_wf/dwi_preproc_ses_202104251808_dir_ap_wf/tensor_estimation_wf/tensor2metric/rd.nii.gz'], ['/media/groot/Yalla/media/MRI/work/single_subject_242_wf/dwi_preproc_ses_202104251808_dir_ap_wf/tensor_estimation_wf/tensor2metric/cl.nii.gz'], ['/media/groot/Yalla/media/MRI/work/single_subject_242_wf/dwi_preproc_ses_202104251808_dir_ap_wf/tensor_estimation_wf/tensor2metric/cp.nii.gz'], ['/media/groot/Yalla/media/MRI/work/single_subject_242_wf/dwi_preproc_ses_202104251808_dir_ap_wf/tensor_estimation_wf/tensor2metric/cs.nii.gz'], ['/media/groot/Yalla/media/MRI/work/single_subject_242_wf/dwi_preproc_ses_202104251808_dir_ap_wf/tensor_estimation_wf/tensor2metric/evec.nii.gz'], ['/media/groot/Yalla/media/MRI/work/single_subject_242_wf/dwi_preproc_ses_202104251808_dir_ap_wf/tensor_estimation_wf/tensor2metric/eval.nii.gz']]
* label : <undefined>
* meta_dict : <undefined>
* modality : <undefined>
* mode : <undefined>
* model : <undefined>
* proc : <undefined>
* reconstruction : <undefined>
* recording : <undefined>
* resolution : <undefined>
* roi : <undefined>
* run : <undefined>
* scans : <undefined>
* session : <undefined>
* source_file : <undefined>
* space : orig
* subject : <undefined>
* subset : <undefined>
* suffix : ['fa', 'adc', 'ad', 'rd', 'cl', 'cp', 'cs', 'evec', 'eval']
* task : <undefined>
* to : <undefined>


Execution Inputs
----------------


* acquisition : <undefined>
* atlas : <undefined>
* base_directory : <undefined>
* ceagent : <undefined>
* check_hdr : True
* cohort : <undefined>
* compress : [True]
* data_dtype : <undefined>
* datatype : tensor
* density : <undefined>
* desc : <undefined>
* direction : <undefined>
* dismiss_entities : <undefined>
* echo : <undefined>
* extension : <undefined>
* fmap : <undefined>
* fmapid : <undefined>
* from : <undefined>
* hemi : <undefined>
* in_file : [['/media/groot/Yalla/media/MRI/work/single_subject_242_wf/dwi_preproc_ses_202104251808_dir_ap_wf/tensor_estimation_wf/tensor2metric/fa.nii.gz'], ['/media/groot/Yalla/media/MRI/work/single_subject_242_wf/dwi_preproc_ses_202104251808_dir_ap_wf/tensor_estimation_wf/tensor2metric/adc.nii.gz'], ['/media/groot/Yalla/media/MRI/work/single_subject_242_wf/dwi_preproc_ses_202104251808_dir_ap_wf/tensor_estimation_wf/tensor2metric/ad.nii.gz'], ['/media/groot/Yalla/media/MRI/work/single_subject_242_wf/dwi_preproc_ses_202104251808_dir_ap_wf/tensor_estimation_wf/tensor2metric/rd.nii.gz'], ['/media/groot/Yalla/media/MRI/work/single_subject_242_wf/dwi_preproc_ses_202104251808_dir_ap_wf/tensor_estimation_wf/tensor2metric/cl.nii.gz'], ['/media/groot/Yalla/media/MRI/work/single_subject_242_wf/dwi_preproc_ses_202104251808_dir_ap_wf/tensor_estimation_wf/tensor2metric/cp.nii.gz'], ['/media/groot/Yalla/media/MRI/work/single_subject_242_wf/dwi_preproc_ses_202104251808_dir_ap_wf/tensor_estimation_wf/tensor2metric/cs.nii.gz'], ['/media/groot/Yalla/media/MRI/work/single_subject_242_wf/dwi_preproc_ses_202104251808_dir_ap_wf/tensor_estimation_wf/tensor2metric/evec.nii.gz'], ['/media/groot/Yalla/media/MRI/work/single_subject_242_wf/dwi_preproc_ses_202104251808_dir_ap_wf/tensor_estimation_wf/tensor2metric/eval.nii.gz']]
* label : <undefined>
* meta_dict : <undefined>
* modality : <undefined>
* mode : <undefined>
* model : <undefined>
* proc : <undefined>
* reconstruction : <undefined>
* recording : <undefined>
* resolution : <undefined>
* roi : <undefined>
* run : <undefined>
* scans : <undefined>
* session : <undefined>
* source_file : <undefined>
* space : orig
* subject : <undefined>
* subset : <undefined>
* suffix : ['fa', 'adc', 'ad', 'rd', 'cl', 'cp', 'cs', 'evec', 'eval']
* task : <undefined>
* to : <undefined>


Execution Outputs
-----------------


* compression : [True, True, True, True, True, True, True, True, True]
* fixed_hdr : [[True], [True], [True], [True], [True], [True], [True], [True], [True]]
* out_file : ['/media/groot/Yalla/media/MRI/derivatives/niworkflows/sub-242/ses-202104251808/tensor/sub-242_ses-202104251808_dir-ap_space-orig_fa.nii.gz', '/media/groot/Yalla/media/MRI/derivatives/niworkflows/sub-242/ses-202104251808/tensor/sub-242_ses-202104251808_dir-ap_space-orig_adc.nii.gz', '/media/groot/Yalla/media/MRI/derivatives/niworkflows/sub-242/ses-202104251808/tensor/sub-242_ses-202104251808_dir-ap_space-orig_ad.nii.gz', '/media/groot/Yalla/media/MRI/derivatives/niworkflows/sub-242/ses-202104251808/tensor/sub-242_ses-202104251808_dir-ap_space-orig_rd.nii.gz', '/media/groot/Yalla/media/MRI/derivatives/niworkflows/sub-242/ses-202104251808/tensor/sub-242_ses-202104251808_dir-ap_space-orig_cl.nii.gz', '/media/groot/Yalla/media/MRI/derivatives/niworkflows/sub-242/ses-202104251808/tensor/sub-242_ses-202104251808_dir-ap_space-orig_cp.nii.gz', '/media/groot/Yalla/media/MRI/derivatives/niworkflows/sub-242/ses-202104251808/tensor/sub-242_ses-202104251808_dir-ap_space-orig_cs.nii.gz', '/media/groot/Yalla/media/MRI/derivatives/niworkflows/sub-242/ses-202104251808/tensor/sub-242_ses-202104251808_dir-ap_space-orig_evec.nii.gz', '/media/groot/Yalla/media/MRI/derivatives/niworkflows/sub-242/ses-202104251808/tensor/sub-242_ses-202104251808_dir-ap_space-orig_eval.nii.gz']
* out_meta : <undefined>


Subnode reports
---------------


 subnode 0 : /home/groot/Projects/dwiprep/trial/ds_native_tensor_wf/ds_native_tensor/mapflow/_ds_native_tensor0/_report/report.rst
 subnode 1 : /home/groot/Projects/dwiprep/trial/ds_native_tensor_wf/ds_native_tensor/mapflow/_ds_native_tensor1/_report/report.rst
 subnode 2 : /home/groot/Projects/dwiprep/trial/ds_native_tensor_wf/ds_native_tensor/mapflow/_ds_native_tensor2/_report/report.rst
 subnode 3 : /home/groot/Projects/dwiprep/trial/ds_native_tensor_wf/ds_native_tensor/mapflow/_ds_native_tensor3/_report/report.rst
 subnode 4 : /home/groot/Projects/dwiprep/trial/ds_native_tensor_wf/ds_native_tensor/mapflow/_ds_native_tensor4/_report/report.rst
 subnode 5 : /home/groot/Projects/dwiprep/trial/ds_native_tensor_wf/ds_native_tensor/mapflow/_ds_native_tensor5/_report/report.rst
 subnode 6 : /home/groot/Projects/dwiprep/trial/ds_native_tensor_wf/ds_native_tensor/mapflow/_ds_native_tensor6/_report/report.rst
 subnode 7 : /home/groot/Projects/dwiprep/trial/ds_native_tensor_wf/ds_native_tensor/mapflow/_ds_native_tensor7/_report/report.rst
 subnode 8 : /home/groot/Projects/dwiprep/trial/ds_native_tensor_wf/ds_native_tensor/mapflow/_ds_native_tensor8/_report/report.rst

