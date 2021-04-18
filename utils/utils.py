# Import libraries
from sklearn.cluster import MeanShift
from operator import itemgetter
import pandas as pd
import numpy as np
import difflib
import json
import cv2
import os


def json_output(save_dir, kw, folder_name):
    """
    Convert keyword dictionary to a json file.

    Arguments:
    save_dir -- string, path for saving output json file.
    kw -- dictionary, keyword dictionary with values.
    folder_name -- string, name for folder contain the json file.

    """

    # Save the output json file in a given path
    with open(os.path.join(save_dir, folder_name + '.json'), "w", encoding='utf8') as outfile:
        json.dump(kw, outfile, indent=6, ensure_ascii=False)


def verification(texts, verf_kw):
    """
    Send verification for searching the page or not.

    Arguments:
    texts -- dictionary, containing image texts.
    verf_kw -- dictionary, keywords to use to confirm the page.

    Return -- boolean, True if the page verified False if not.

    """
    score = 0
    # Iterate over texts
    for word in verf_kw:
        # check how many of the words in this page is in our verf_kw list
        if word in texts:
            score += 1
        else:
            continue

    # if it pass the threshold return True else return False
    if score >= len(verf_kw) - 1:
        return True
    else:
        return False


def line_correction(df):
    """
    Correct the arrangement of lines

    Arguments:
    df -- pandas dataframe, a dataframe contain information of current page

    Return:
    df -- pandas dataframe, a dataframe contain information of current page with correct lines
    """

    # Convert lines from dataframe to a list
    lines = list(df['line'])

    # Define a variable for separating first line from other lines
    score = 0

    # Iterate over lines
    for index in range(len(lines)):

        # check the lines for changing
        if lines[index] == 1:
            score += 1

        # if the line equal to 1 and is not the first line
        if lines[index] >= 1 and score > 1:

            if lines[index] == list(df['line'])[index - 1]:
                lines[index] = lines[index - 1]  # equal the line to the previous line
            else:
                lines[index] = lines[index - 1] + 1  # equal the line to the previous line + 1

    df['line'] = lines

    return df


def remove_lines(image, horizontal=True, vertical=True, thick=3):
    """
    Remove the lines inside an image.

    Arguments:
    image -- numpy array, array of the given image.
    horizontal -- boolean, weather perform horizontal removal or not.
    vertical -- boolean, weather perform vertical removal or not.
    thick -- integer, thickness of the lines in the page

    Returns:
    image -- numpy array, return array of the image without lines.

    """

    # Convert the image to grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    # Perform an otsu thresholding on the image
    otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

    # Detect the horizontal lines if the horizontal value is set to True
    if horizontal:
        # create a kernel to find lines
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
        # detect lines with created kernel
        detected_horizontal = cv2.morphologyEx(otsu, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
        # find horizontal contours of the image
        cnts_ho = cv2.findContours(detected_horizontal, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        # draw white lines on detected lines to cover them
        cnts_ho = cnts_ho[0] if len(cnts_ho) == 2 else cnts_ho[1]
        for c in cnts_ho:
            cv2.drawContours(image, [c], -1, (255, 255, 255), thick)

    # Detect the vertical lines if the vertical value is set to True
    if vertical:
        # create a kernel to find lines
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 25))
        # detect lines with created kernel
        detected_vertical = cv2.morphologyEx(otsu, cv2.MORPH_OPEN, vertical_kernel, iterations=2)
        # find vertical contours of the image
        cnts_ve = cv2.findContours(detected_vertical, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        # draw white lines on detected lines to cover them
        cnts_ve = cnts_ve[0] if len(cnts_ve) == 2 else cnts_ve[1]
        for c in cnts_ve:
            cv2.drawContours(image, [c], -1, (255, 255, 255), thick)

    return image


def json_accuracy(pdf_dir, kw, ref_dir):
    """
    Find the accuracy of all keywords in all files
    Arguments:
    pdf_df -- string, a path to the pdf files
    kw -- dictionary, contain keywords
    ref_dir -- string, path to the reference json files.
    """
    acc = {}

    # define path of extracted jsons and reference jsons.
    ext_json = os.path.join(pdf_dir, 'json')
    ref_json = ref_dir

    # iterate over keywords in kw dictionary
    for keyword in kw.keys():

        tru = 0
        total = 0

        if keyword != 'accuracy':

            # iterate over keywords in dictionaries
            for file in sorted(os.listdir(ext_json)):

                # open both files
                with open(os.path.join(ext_json, file)) as json1:
                    dic1 = json.load(json1)
                with open(os.path.join(ref_json, file)) as json2:
                    dic2 = json.load(json2)

                # compare keywords in each file
                if difflib.SequenceMatcher(None, dic2[keyword].lower(), dic1[keyword].lower()).ratio() > 0.80:
                    tru += 1

                total += 1

            # create a json file which contain accuracy of each keyword over all extracted jsons
            acc[keyword] = round(tru / total, 3)

    json_output(pdf_dir, acc, 'Accuracy')


def find_lines(img):
    """
    Find lines in a documents

    Arguments:
    img -- string or array, image to find lines
    """

    line_list = []

    if type(img) is str:
        img = cv2.imread(img)

    image = img.copy()

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

    # create a kernel to find lines
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
    # detect lines with created kernel
    detected_horizontal = cv2.morphologyEx(otsu, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
    # find horizontal contours of the image
    cnts_hor = cv2.findContours(detected_horizontal, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # draw white lines on detected lines to cover them
    cnts_ho = cnts_hor[0] if len(cnts_hor) == 2 else cnts_hor[1]

    for c in cnts_ho:
        [x1, y1], [x2, y2] = c[0][0], c[1][0]
        line_list.append([x1, y1])

    sort_lines = sorted(line_list, key=itemgetter(1))

    return sort_lines


def _find_lines(dataframe: pd.DataFrame, **kwargs):
    if 'bandwidth' in kwargs.keys():
        clustering = MeanShift(bandwidth=kwargs['bandwidth'])
    else:
        clustering = MeanShift(bandwidth=8)

    y_mean = ((dataframe['top'] - (dataframe['height']/2)) + dataframe['height']) // 2
    y_mean = np.sort(y_mean)
    y_mean = np.expand_dims(y_mean, axis=1)

    clustering.fit(y_mean)
    labels = clustering.labels_
    labels_ = np.zeros(labels.shape, dtype=np.uint8)
    _, idx = np.unique(labels, return_index=True)
    uniques = labels[np.sort(idx)]
    for i, label in enumerate(uniques):
        labels_[labels == label] = i

    return labels_, y_mean


def find_text_lines(dataframe: pd.DataFrame, **kwargs):
    lines, y_mean = _find_lines(dataframe, **kwargs)
    dataframe['line'] = lines

    return dataframe
