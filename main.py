# Import libraries_
from shutil import rmtree
from tqdm import tqdm
import argparse
import os

from pdf_processing import convert_pdf_to_text, json_only
from configures import configs


def main():
    # Define the input arguments
    ap = argparse.ArgumentParser()

    ap.add_argument("-pdf_dir", "--pdf_directory", required=True, help="path to load the pdf files")
    ap.add_argument("-form", "--form_name", required=False, default=None, help="the format of the forms e.g. ergo ...")

    # Convert arguments to a dictionary
    args = vars(ap.parse_args())

    # Denote each argument to a variable
    pdf_dir = r'{}'.format(args['pdf_directory'])
    form_type = args['form_name']
    oj = configs['only_json']

    # Make a temporary file for saving outputs
    if oj:
        if 'OUTPUT' not in os.listdir(pdf_dir):
            os.mkdir(os.path.join(pdf_dir, 'OUTPUT'))
        else:
            rmtree(os.path.join(pdf_dir, 'OUTPUT'))
            os.mkdir(os.path.join(pdf_dir, 'OUTPUT'))

    elif 'temp' not in os.listdir(pdf_dir) and 'OUTPUT' not in os.listdir(pdf_dir) and not oj:
        os.mkdir(os.path.join(pdf_dir, 'temp'))
        os.mkdir(os.path.join(pdf_dir, 'OUTPUT'))

    else:
        rmtree(os.path.join(pdf_dir, 'temp'))
        rmtree(os.path.join(pdf_dir, 'OUTPUT'))
        os.mkdir(os.path.join(pdf_dir, 'temp'))
        os.mkdir(os.path.join(pdf_dir, 'OUTPUT'))

    # Iterate over files in given directory
    for pdf_file in tqdm(sorted(os.listdir(pdf_dir)), bar_format='{l_bar}{bar:50}{r_bar}{bar:-50b}'):
        if pdf_file.lower().endswith('.pdf'):
            if oj:
                json_only(pdf_dir, pdf_file, form_type)
            else:
                convert_pdf_to_text(pdf_dir, form_type, pdf_file)


if __name__ == '__main__':
    main()
