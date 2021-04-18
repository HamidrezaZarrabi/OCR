# Import libraries
from cv2 import cv2
import pandas as pd
import pytesseract
import pdf2image
# import tr

from utils.utils import line_correction, find_lines, remove_lines, json_output, find_text_lines
from forms import bauleistung
from utils.my_functions import clean_lines
from utils.page_utils import *
from configures import configs
from utils.page import Page


class PDFFile:

    def __init__(self, pdf_direcotry, name, save_path):

        self.pdf_directory = pdf_direcotry
        self.save_path = save_path
        self.name = name
        pd.options.mode.chained_assignment = None
        self.main_dict = {}

    def split_pages(self):
        """
        Split each pdf to it pages.
        """
        pages = {}

        file_path = os.path.join(self.pdf_directory, self.name)

        pdfs = pdf2image.convert_from_path(file_path)

        for ii in range(len(pdfs)):

            if ii < 9:  # name each page after number of pdf file page
                page_number = f'00{ii + 1}'
            elif ii < 99:
                page_number = f'0{ii + 1}'
            else:
                page_number = f'{ii + 1}'

            # output each page to image directory
            pages[f"page_{page_number}.pdf"] = pdfs[ii]

        self.main_dict['pages'] = pages

    def page_to_image(self):
        """
        Convert each page of the pdf file to image

        Arguments:
        filter_function -- function, preprocess function for images.
        """

        pages = self.main_dict['pages']

        images = {}
        pp_images = {}

        # Iterate over pages
        for page in pages.keys():

            image_name = page[:-4] + '.jpeg'

            open_cv_image = np.array(pages[page])
            cv_image = open_cv_image[:, :, ::-1].copy()

            path_image = os.path.join(self.save_path, image_name)
            path_pp_image = os.path.join(self.save_path, 'PP_' + image_name)

            pp_image = processing_image(cv_image)

            # Save image of each page
            if configs['save_images']:
                cv2.imwrite(path_image, cv_image)
            if configs['save_pp_images']:
                cv2.imwrite(path_pp_image, pp_image)

            images[image_name] = cv_image
            pp_images[image_name] = pp_image

        self.main_dict['images'] = images
        self.main_dict['pp_images'] = pp_images

    def image_to_output(self):
        """
        Convert images to specified output format.

        Arguments:
        ocr_engine -- string, choose the ocr engine.(tesseracts, tr-ocr)
        image -- numpy array, image array.
        output_type -- string, type of the output.
        find_line -- bool, if true program return vertical lines as well
        coordinates_of_the_word -- string, choose the coordinate of the word.(left, middle)

        Returns:
        df -- pandas dataframe, contain information of the page.
        """

        # Read configurations from config file
        ocr_engine = configs['ocr_engine']
        output_type = configs['output_type']
        find_line = configs['find_lines']
        coordinates = configs['coordinates_of_the_words']
        process = configs['process_image']

        dfs = {}

        org_img = self.main_dict['images']

        if process:
            images = self.main_dict['pp_images']
        else:
            images = org_img

        for j, imagee in enumerate(images.values()):

            image = imagee.copy()
            df = pd.DataFrame(columns=['text', 'left', 'top', 'width', 'height', 'line', 'block', 'l-r', 'u-d', 'conf'])

            name = list(images.keys())[j][:-5]

            if ocr_engine is 'trocr':

                df = tr_ocr(image, df, coordinates)
                if type(df) is bool:
                    continue

            else:

                df = tesseracts_ocr(image, df, coordinates)
                if type(df) is bool:
                    continue

            df = add_block(df, image)

            block_name = 'Block_' + list(images.keys())[j]

            file_name = os.path.join(self.save_path, block_name)

            if configs['save_block_image']:
                cv2.imwrite(file_name, image)

            if find_line:

                line_list = find_lines(tuple(org_img.values())[j])

                lines = clean_lines(line_list)

                for i in range(len(lines)):
                    df = df.append({'text': '<LINE>', 'top': lines[i][1], 'left': lines[i][0]},
                                   ignore_index=True)

            if type(df) is pd.core.frame.DataFrame:
                pass
            else:
                continue

            df = df.fillna(-1)
            df['line'] = df['line'].apply(np.int64)
            df['block'] = df['block'].apply(np.int64)

            if output_type == 'excel':
                dfs[name + 'xlsx'] = df
                df.to_excel(os.path.join(self.save_path, name + '.xlsx'))

            elif output_type == 'csv':
                dfs[name + 'csv'] = df
                df.to_csv(os.path.join(self.save_path, name + '.csv'))

            else:
                dfs[name] = df

        self.main_dict['dfs'] = dfs


def tr_ocr(image, df, coordinates_of_the_word):
    """
    Convert the tr outputs to dataframe

    Arguments:
    image_path -- string, path for image to load.
    coordinates_of_the_word -- string, coordinates of the word.(left or middle)

    Returns:
    df -- pandas dataframe, contain information of the page.
    """

    # Preprocess the images with preprocess function
    pp_img = cv2.imread(image, cv2.IMREAD_GRAYSCALE)

    # if open-cv can not read the image, program read it with matplotlib
    H, W = pp_img.shape

    # extract the middle points of the page
    Hmid = int(H / 2)
    Wmid = int(W / 2)

    tr_info = tr.run(image)

    if len(tr_info) < 10:
        return False

    # iterate over returned values from tr ocr
    for i in range(len(tr_info)):

        if tr_info[i][1] == '':
            continue
        else:
            pass

        # extract the location of texts
        (cor_list, t, c) = (tr_info[i])
        [x, y, w, h, _] = cor_list

        if x > Wmid:
            l_r = 1
        else:
            l_r = 0

        if y > Hmid:
            u_d = 1
        else:
            u_d = 0

        if coordinates_of_the_word == 'middle':
            xbar = x - (w / 2)
            ybar = y - (h / 2)
        else:
            xbar = x
            ybar = y

        df = df.append({'text': t,
                        'left': int(xbar),
                        'top': int(ybar),
                        'width': int(w),
                        'height': int(h),
                        'l-r': l_r,
                        'u-d': u_d,
                        'conf': c},
                       ignore_index=True)

    df_new = find_text_lines(df)
    df_new = df_new.append({'text': '<END>', 'left': W, 'top': H}, ignore_index=True)

    return df_new


def tesseracts_ocr(pp_img, df, coordinates_of_the_word):
    """
    Convert tesseracts outputs to dataframe.

    Arguments:
    image -- string, path to load the image.
    coordinates_of_the_word -- string, coordinates of the word.(left or middle)

    Returns:
    df -- pandas dataframe, contain information of the page.
    """

    tess_config = r'--psm 6 -l deu'

    # if open-cv can not read the image, program read it with matplotlib
    H, W = pp_img.shape[0], pp_img.shape[1]

    # extract the middle points of the page
    Hmid = int(H / 2)
    Wmid = int(W / 2)

    tess_img = pytesseract.image_to_data(pp_img, output_type=pytesseract.Output.DICT,
                                         config=tess_config)

    n_boxes = len(tess_img['text'])

    if n_boxes < 10:
        return False
    else:
        # iterate over extracted texts for output as excel file
        for i in range(n_boxes):

            if tess_img['text'][i] == '':  # Remove spaces
                continue
            else:
                # extract information of each text recognized by tesseract
                (t, x, y, w, h, l, c) = (tess_img['text'][i],
                                         tess_img['left'][i],
                                         tess_img['top'][i],
                                         tess_img['width'][i],
                                         tess_img['height'][i],
                                         tess_img['line_num'][i],
                                         tess_img['conf'][i])
                # this line is used if we wand to draw rectangle around each word
                # cv2.rectangle(test_img, (x, y), (x+w, y+h), (255,255,0), 2)

                if int((w / 2) + x) > Wmid:
                    l_r = 1
                else:
                    l_r = 0

                if int(y) > Hmid:
                    u_d = 1
                else:
                    u_d = 0

                if coordinates_of_the_word == 'middle':
                    xbar = x + (w / 2)
                    ybar = y + (h / 2)
                else:
                    xbar = x
                    ybar = y

                # append the extracted data from image to created dataframe
                df = df.append({'text': t,
                                'left': xbar,
                                'top': ybar,
                                'width': w,
                                'height': h,
                                'line': l,
                                'l-r': l_r,
                                'u-d': u_d,
                                'conf': c},
                               ignore_index=True)

        # Correct the lines with defined function
        df_correct = line_correction(df)

    df_correct = df_correct.append({'text': '<END>', 'left': W, 'top': H}, ignore_index=True)

    return df_correct


def find_and_correct_lines(df, line_list):
    """
    Find and remove extra horizontal lines from document

    Arguments:
    df -- pandas dataframe, a dataframe which contain the data from page
    line_list -- list, contain lines in page

    Return:
    df -- pandas dataframe, modified data frames with lines
    """

    df_correct = df.copy()

    lines = clean_lines(line_list)

    for i in range(len(sorted(lines))):
        val = df[df['top'] < lines[i]]
        val1 = val[val['top'] > lines[i] - 8]
        if not list(val1['text']):
            df_correct = df_correct.append({'text': '<LINE>', 'top': lines[i]}, ignore_index=True)

    return df_correct


def add_block(df, img):
    """
    Add blocks information to dataframe.

    Args:
        df: pandas dataframe, contain information of page
        img: array, image of the page.

    Returns:
        df: pandas dataframe, information of page with block ids.
    """

    page = Page(img)
    segmented_rects, _ = page.crop()

    for i, rects in enumerate(segmented_rects):
        cv2.rectangle(img, (rects[0], rects[1]), (rects[2], rects[3]), (0, 0, 255), 3)

        bool_series = df[
            (df['left'] > rects[0]) & (df['left'] < rects[2]) & (df['top'] > rects[1]) & (df['top'] < rects[3])]

        bool_series.loc[:, 'block'] = i + 1

        df.update(bool_series)

    return df


def processing_image(img):
    """
    Perform preprocessing tasks on image to remove noises with openCV.

    Arguments:
    img -- string, path of an image which want to perform preprocessing on it.

    Return:
    image -- numpy array, array of output image which performed preprocessing tasks on it.
    """
    if type(img) is not str:

        image = img.copy()
        # image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    else:

        image = cv2.imread(img)  # Convert RGB image to grayscale

    image = remove_lines(image, horizontal=True, vertical=True, thick=3)

    # Setting all background pixels to 0 and foreground pixels to 255
    # image = cv2.threshold(image, 127, 255, cv2.THRESH_BINARY)[1]

    return image


def convert_pdf_to_text(pdf_directory, form_type, pdf_file):
    """
    Convert pdf files to specified output format

    Arguments:
        pdf_directory: string, path to load pdf files.
        form_type: string, type of form for ocr.
        pdf_file: string, name of the pdf_file
    """
    # Create temp path for saving images and dataframes
    save_path = os.path.join(os.path.join(pdf_directory, 'temp'), pdf_file[:-4])
    os.mkdir(save_path)
    # Create output path for saving jsons
    save_output = os.path.join(pdf_directory, 'OUTPUT')

    form_dict = {'bauleistung': bauleistung}

    # Create an instance of the class
    pdf = PDFFile(pdf_directory, pdf_file, save_path)

    pdf.split_pages()

    pdf.page_to_image()

    pdf.image_to_output()

    df_list = list(pdf.main_dict['dfs'].values())

    if form_type:
        kw = form_dict[form_type].find_values(pdf.main_dict, pdf_file)

        json_output(save_output, kw, pdf_file[:-4])


def json_only(pdf_directory, pdf_file, form_type):
    """

    Args:
        pdf_directory: string, path to the pdf files
        pdf_file: string,, name of the pdf file
        form_type: string, type of the form
    """
    df_list = {}
    images = {}
    pp_images = {}
    main_dict = {}

    form_dict = {'bauleistung': bauleistung}

    save_path = os.path.join(os.path.join(pdf_directory, 'temp'), pdf_file[:-4])
    save_output = os.path.join(pdf_directory, 'OUTPUT')

    for item in sorted(os.listdir(save_path)):
        if item.endswith('.xlsx'):
            excel_path = os.path.join(save_path, item)

            df = pd.read_excel(excel_path, engine='openpyxl')
            df = df.drop(columns=['Unnamed: 0'], axis=1)
            df['text'] = df['text'].apply(str)

            if configs['pass_dictionary']:
                image_name = item[:-4] + 'jpeg'
                pp_image_name = 'PP_' + item[:-4] + 'jpeg'
                image_path = os.path.join(save_path, image_name)
                pp_image_path = os.path.join(save_path, pp_image_name)

                image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
                pp_image = cv2.imread(pp_image_path, cv2.IMREAD_GRAYSCALE)

                images[image_name] = image
                pp_images[pp_image_name] = pp_image

            df_list[item] = df

    main_dict['images'] = images
    main_dict['pp_images'] = pp_images
    main_dict['dfs'] = df_list

    if configs['pass_dictionary']:
        kw = form_dict[form_type].find_values(main_dict, pdf_file)
    else:
        kw = form_dict[form_type].find_values(df_list, pdf_file)

    json_output(save_output, kw, pdf_file[:-4])
