configs = {
    'save_block_image': True,
    'save_images': True,
    'save_pp_images': True,
    'ocr_engine': 'tesseract',  # Choose OCR engine between tesseracts and TrOCR
    'output_type': 'excel',  # Choose the OCR output
    'find_lines': True,  # Whether to find horizontal lines and put in output files or not
    'coordinates_of_the_words': 'middle',  # Choose the which coordinate of words to be saved.(middle or left)
    'only_json': True,  # Whether do OCR process from beginning or just filling json file
    'process_image': True,  # Weather process images before OCR or not
    'revision_file_path_for_tr_extraction': '/home/deep/Workspace/Data/ocr/Revision/temp',  # path for Tr to read images
                                                                                            # this is just for Revision
    'kfz_file_path': '/home/deep/Workspace/Data/ocr/Versicherungsbestätigungen/temp',
    'pass_dictionary': True #
}
