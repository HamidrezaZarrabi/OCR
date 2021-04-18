# Import libraries
from utils.utils import json_output, verification, remove_lines, word_similarity
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import cv2
import re
import os


def processing_image_allianz(img):
    """
    Perform preprocessing tasks on image to remove noises with openCV.

    Arguments:
    img -- string, path of an image which want to perform preprocessing on it.

    Return:
    image -- numpy array, array of output image which performed preprocessing tasks on it.

    """

    gray = cv2.imread(img, cv2.IMREAD_GRAYSCALE)  # Convert RGB image to grayscale

    if gray is None:
        image_raw = plt.imread(img)  # Cv2 might not read the image so read it with plt
        gray = cv2.cvtColor(image_raw, cv2.COLOR_RGB2GRAY)  # Convert the plt image to grayscale

    image = remove_lines(gray, horizontal=True, vertical=True)

    # Setting all background pixels to 0 and foreground pixels to 255
    image = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    image = cv2.medianBlur(image, 3)  # Remove noises in the image with median blur
    image = cv2.dilate(image, np.ones((1, 1), np.uint8), iterations=1)  # Dilation
    image = cv2.erode(image, np.ones((1, 1), np.uint8), iterations=2)  # Erosion
    image = cv2.morphologyEx(image, cv2.MORPH_OPEN, np.ones((1, 1), np.uint8))

    return image


def ret_allianz():
    """
    Defining custom keywords in function

    Return:
    keywords -- dictionary, contain all defined keywords
    verf_list -- list, contain page verification keywords
    diff_list -- list, contain important words to correct in case of mis recognizing
    """

    keywords = {"Es betreut Sie": []
        , "Kfz-Versicherung": []
        , "Versicherungsschein": []
        , "Aufhebungsnachtrag": []
        , "Versicherungsnehmer": []
        , "Versichertes Fahrzeug": []
        , "Kennzeichen": []
        , "Fahrzeug-ldentifizierungs-Nummer": []
        , "Kfz-Haftpflichtversicherung": []
        , "Kaskoversicherung": {"Vollkaskoversicherung": []
            , "Teilkaskoversicherung": []}
        , "Kfz-Haftpflichtvers 1": []
        , "Kaskovers 1": []
        , "Kfz-Haftpflichtvers 2": []
        , "Kaskovers 2": []
        , "Kfz-Haftpflichtvers 3": []
        , "Kaskovers 3": []
        , "Kfz-Haftpflichtvers 4": []
        , "Kaskovers 4": []
        , "Kfz-Haftpflichtvers 5": []
        , "Kaskovers 5": []}

    verf_list = {"p1": ["Fahrzeug-ldentifizierungs-Nummer", "Firmenverbindung", "Kaskoversicherung", "Kfz-Versicherung"]
        , "p2": ["Kfz-Haftpflichtvers", "Versicherungsnehmer", "Kaskovers", "Zwischensumme"]}

    diff_list = ["Kfz-Versicherung", "Versicherungsnehmer", "Versicherungsschein", "Kennzeichen", "Amtliches"
        , "Fahrzeug-ldentifizierungs-Nummer", "Kfz-Haftpflichtversicherung", "Kaskoversicherung", "Aufbauart"
        , "Vollkaskoversicherung", "Teilkaskoversicherung", "Kfz-Haftpflichtvers", "Zwischensumme", "Kaskovers"
        , "Aufbauart"]

    return keywords, verf_list, diff_list


def first_page_allianz(df, kw):
    """
    Custom structures of the first page of allianz forms

    Arguments:
    df -- pandas dataframe, a dataframe which contain information of the first page
    kw -- dictionary, dictionary of keywords

    Return:
    kw -- dictionary, contain keywords and values of first page
    """

    # Iterate over texts in dataframe and with the defined structure for each keyword, extract the output value
    for index in range(len(df['text'])):

        if re.sub('[\W_]+', '', df['text'][index]) == "KfzVersicherung" and kw["Kfz-Versicherung"] == []:
            if df['text'][index+2] == "Versicherungsnehmer":
                kw["Kfz-Versicherung"] = df['text'][index + 1]
            else:
                kw["Kfz-Versicherung"] = df['text'][index+1] + ' ' + df['text'][index+2]

        elif df['text'][index] == "betreut" and df['text'][index - 1] == "Es":
            val = df[df['left'] > df['left'][index - 1] - 20]
            val1 = val[val['top'] > df['top'][index]]
            val2 = val1[val1['line'] <= df['line'][index] + 3]
            kw["Es betreut Sie"] = ' '.join(list(val2['text']))

        elif df['text'][index] == "Versicherungsnehmer" and not kw["Versicherungsnehmer"]:
            val = df[df['top'] > df['top'][index]]
            val1 = val[val['left'] < df['left'][index] + df['width'][index] + 50]
            val2 = val1[val1['left'] > df['left'][index] - 20]
            for i in range(len(val2['text'])):
                if df['text'][i] == "Firmenverbindung":
                    kw["Versicherungsnehmer"] = ' '.join(list(val2.loc[:i-1, 'text']))
                    # [' '.join(list(val2[val2['line'] == line]['text'])) for line in sorted(set(list(val2['line'])))][0]

        elif df['text'][index] == "Fahrzeug" and df['text'][index - 1] == "Versichertes":

            if "Aufbauart" in list(df[df['line'] == df['line'][index]]['text']):
                i = list(df[df['line'] == df['line'][index]]['text']).index("Aufbauart")
                j = list(df[df['line'] == df['line'][index]]['text']).index("Fahrzeug")
                kw["Versichertes Fahrzeug"] = ' '.join(list(df[df['line'] == df['line'][index]]['text'])[j+1:i])
            elif "Aufbauart" in list(df[df['line'] == df['line'][index] + 1]['text']):
                i = list(df[df['line'] == df['line'][index] + 1]['text']).index("Aufbauart")
                kw["Versichertes Fahrzeug"] = ' '.join(list(df[df['line'] == df['line'][index] + 1]['text'])[:i])
            elif "Amtliches" in list(df[df['line'] == df['line'][index] + 1]['text']):
                i = list(df[df['line'] == df['line'][index] + 1]['text']).index("Amtliches")
                kw["Versichertes Fahrzeug"] = ' '.join(list(df[df['line'] == df['line'][index] + 1]['text'])[:i])
            elif "Kennzeichen" in list(df[df['line'] == df['line'][index]]['text']):
                kw["Versichertes Fahrzeug"] = df['text'][index+1]

        elif df['text'][index] == "Kennzeichen" and df['text'][index - 1] == "Amtliches":
            kw["Kennzeichen"] = df['text'][index+1] + ' ' + df['text'][index+2]

        elif df['text'][index] == "Fahrzeug-ldentifizierungs-Nummer":
            kw["Fahrzeug-ldentifizierungs-Nummer"] = df['text'][index + 1]

        elif df['text'][index] == "Kfz-Haftpflichtversicherung" and not kw["Kfz-Haftpflichtversicherung"]:

            for i in range(len(df['text'])):
                if df['text'][i] == "Kaskoversicherung" and df['text'][i] == list(
                        df[df['line'] == df['line'][i]]['text'])[0]:
                    val = df[df['top'] > df['top'][index] + 10]
                    val1 = val[val['top'] < df['top'][i] - 10]
                    kw["Kfz-Haftpflichtversicherung"] = ' '.join(list(val1['text']))

        elif df['text'][index] == "Kaskoversicherung":
            if "Vollkaskoversicherung" in list(df[df['line'] == df['line'][index] + 1]['text']):
                kw["Kaskoversicherung"]["Vollkaskoversicherung"] = ' '.join(
                    list(df[df['line'] == df['line'][index] + 1]['text'])[-2:])
            if "Teilkaskoversicherung" in list(df[df['line'] == df['line'][index] + 2]['text']):
                kw["Kaskoversicherung"]["Teilkaskoversicherung"] = ' '.join(
                    list(df[df['line'] == df['line'][index] + 2]['text'])[-2:])

            if "Kaskoversicherung" in list(df[df['line'] == df['line'][index] + 1]['text']):
                try:
                    i = list(df[df['line'] == df['line'][index] + 1]['text']).index("Kaskoversicherung")
                    kw["Kaskoversicherung"]["_"] = ' '.join(
                        list(df[df['line'] == df['line'][index] + 1].iloc[i + 1:]['text']))
                except ValueError as ve:
                    pass

    return kw


def second_page_allianz(df, kw):
    """
    Custom structures of the second page of allianz forms

    Arguments:
    df -- pandas dataframe, a dataframe which contain information of the second page
    kw -- dictionary, dictionary of keywords

    Return:
    kw -- dictionary, contain keywords and values of second page
    """

    num = list(df['text']).count("Kfz-Haftpflichtvers")

    for index in range(len(df['text'])):

        if df['text'][index] == "Kfz-Haftpflichtvers" and not kw["Kfz-Haftpflichtvers 1"]:
            kw["Kfz-Haftpflichtvers 1"] = list(df[df['line'] == df['line'][index]]['text'])[-1]

            if "Kaskovers" in list(df[df['line'] == df['line'][index] + 1]['text']):
                kw["Kaskovers 1"] = list(df[df['line'] == df['line'][index] + 1]['text'])[-1]

                if num == 1:
                    break

        elif df['text'][index] == "Kfz-Haftpflichtvers" and kw["Kfz-Haftpflichtvers 1"] != [] and not kw["Kfz-Haftpflichtvers 2"]:
            if len(list(df[df['line'] == df['line'][index]]['text'])[-1]) <= 1:
                kw["Kfz-Haftpflichtvers 2"] = list(df[df['line'] == df['line'][index]]['text'])[-2]
            else:
                kw["Kfz-Haftpflichtvers 2"] = list(df[df['line'] == df['line'][index]]['text'])[-1]

            if "Kaskovers" in list(df[df['line'] == df['line'][index] + 1]['text']):
                kw["Kaskovers 2"] = list(df[df['line'] == df['line'][index] + 1]['text'])[-1]

                if num == 2:
                    break

        elif df['text'][index] == "Kfz-Haftpflichtvers" and kw["Kfz-Haftpflichtvers 2"] != [] and not kw["Kfz-Haftpflichtvers 3"]:
            kw["Kfz-Haftpflichtvers 3"] = list(df[df['line'] == df['line'][index]]['text'])[-1]

            if "Kaskovers" in list(df[df['line'] == df['line'][index] + 1]['text']):
                kw["Kaskovers 3"] = list(df[df['line'] == df['line'][index] + 1]['text'])[-1]

                if num == 3:
                    break

        elif df['text'][index] == "Kfz-Haftpflichtvers" and kw["Kfz-Haftpflichtvers 3"] != [] and not kw["Kfz-Haftpflichtvers 4"]:
            kw["Kfz-Haftpflichtvers 4"] = list(df[df['line'] == df['line'][index]]['text'])[-1]

            if "Kaskovers" in list(df[df['line'] == df['line'][index] + 1]['text']):
                kw["Kaskovers 4"] = list(df[df['line'] == df['line'][index] + 1]['text'])[-1]

                if num == 4:
                    break

        elif df['text'][index] == "Kfz-Haftpflichtvers" and kw["Kfz-Haftpflichtvers 4"] != [] and not kw["Kfz-Haftpflichtvers 5"]:
            kw["Kfz-Haftpflichtvers 5"] = list(df[df['line'] == df['line'][index]]['text'])[-1]

            if "Kaskovers" in list(df[df['line'] == df['line'][index] + 1]['text']):
                kw["Kaskovers 5"] = list(df[df['line'] == df['line'][index] + 1]['text'])[-1]

                if num == 5:
                    break


    return kw


def find_values_allianz(pdf_dir):
    """
    Finds values of given keywords in allianz forms and pass the values to another function for converting to json.

    Arguments:
    pdf_dir -- string, path to the pdf files want to read.

    """

    excel_dir = os.path.join(pdf_dir, 'excel')

    for folder in os.listdir(excel_dir):

        kw = ret_allianz()[0] # load the keywords

        for excel_file in os.listdir(os.path.join(excel_dir, folder)):
            excel = os.path.join(os.path.join(excel_dir, folder), excel_file)

            # convert excels to pandas dataframe
            df_raw = pd.read_excel(excel).drop(['Unnamed: 0'], axis=1)

            df_raw['text'] = df_raw['text'].apply(str)

            df_correct = word_similarity(df_raw, ret_allianz()[2])

            if verification(df_correct['text'], ret_allianz()[1]['p1']):

                try:
                    index_word = list(df_correct['text']).index("Versicherungsschein")
                    df = df_correct[df_correct['left'] > df_correct.iloc[index_word]['left'] - 20].reset_index()
                    if len(df) == 0:
                        index_word = list(df_correct['text']).index("Kfz-Versicherung")
                        df = df_correct[df_correct['left'] > df_correct.iloc[index_word]['left'] - 20].reset_index()
                except:
                    df = df_correct

                kw = first_page_allianz(df, kw)

            elif verification(df_correct['text'], ret_allianz()[1]['p2']):

                try:
                    index_word = list(df_correct['text']).index("Kfz-Haftpflichtvers")
                    df = df_correct[df_correct['left'] > df_correct.iloc[index_word]['left'] - 20].reset_index()
                    if len(df) == 0:
                        index_word = list(df_correct['text']).index("Zwischensumme")
                        df = df_correct[df_correct['left'] > df_correct.iloc[index_word]['left'] - 20].reset_index()
                except:
                    df = df_correct

                kw = second_page_allianz(df, kw)

        json_output(pdf_dir, kw, folder)