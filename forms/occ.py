# Import libraries
from utils.utils import json_output, word_similarity
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import cv2
import re
import os


def preprocess_image_occ(img):
    """
    Perform preprocessing tasks on image to remove noises with openCV.

    Arguments:
    img -- string, path of an image which want to perform preprocessing on it.

    Return:
    image -- numpy array, array of output image which performed preprocessing tasks on it.

    """
    image = cv2.imread(img, cv2.IMREAD_GRAYSCALE)  # Convert RGB image to grayscale

    if image is None:
        image = plt.imread(img)  # Cv2 might not read the image so read it with plt
        image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)  # Convert the plt image to grayscale

    image = cv2.medianBlur(image, 1)  # Remove noises in the image with median blur
    # Setting all background pixels to 0 and foreground pixels to 255
    image = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    image = cv2.dilate(image, np.ones((1, 1), np.uint8), iterations=1)  # Dilation
    image = cv2.erode(image, np.ones((1, 1), np.uint8), iterations=2)  # Erodsion
    image = cv2.morphologyEx(image, cv2.MORPH_OPEN, np.ones((1, 1), np.uint8))

    return image


def ret_kw_occ():
    """
    Defining custom keywords in function

    Return:
    keywords -- dictionary, contain all defined keywords
    verf_list -- list, contain page verification keywords
    diff_list -- list, contain important words to correct in case of mis recognizing
    """

    keywords = {"Frau": {"1": [], "2": [], "3": [], "4": []}
        , "Es betreut Sie": []
        , "Versicherungsschein Nr": []
        , "Ihr Ansprechpartner": []
        , "Vertragsbeginn": []
        , "Vertragsablauf": []
        , "Zahlweise": []
        , "Änderungsart": []
        , "Hersteller": []
        , "Fahrzeugart": []
        , "Typ": []
        , "Historische Kennzeichen": []
        , "Erstzulassung": []
        , "Fahrgestellnummer": []
        , "Motorenstärke": []
        , "Pauschalversicherungssumme": []
        , "Deckung": []
        , "Selbstbeteiligung": {"Teilkasko": []}}

    verf_kw = []

    diff_list = ["occ@occ.eu", "www.occ.eu", "Assekuradeur", "Ansprechpartner", "Vertragsbeginn", "Vertragsablauf"
        , "Fahrgestellnummer", "Motorenstärke", "Pauschalversicherungssumme", "Selbstbeteiligung", "Liebhaberfahrzeuge"
        , "Fahrgestellnummer", "Erstzulassung", "Kennzeichen", "OCC-Beitragsrechnung"]

    return keywords, verf_kw, diff_list


def first_page_occ(df, kw):
    """
    Custom structures of the first page of occ forms

    Arguments:
    df -- pandas dataframe, a dataframe which contain information of the first page
    kw -- dictionary, dictionary of keywords
    """

    # Iterate over texts in dataframe and with the defined structure for each keyword, extract the output value
    for index in range(len(df['text'])):

        if df['text'][index] == "Frau" and df['text'][index] == list(df[df['line'] == df['line'][index]]['text'])[0]:
            val = df[df['top'] > df['top'][index]]
            val1 = val[val['left'] < df['left'][index] + 600]
            val2 = val1[val1['top'] < df['top'][index] + 250]
            val_list = [" ".join(val2[val2['line'] == line]['text']) for line in sorted(set(list(val2['line'])))]

            if len(val_list) == 3:
                kw["Frau"]["1"] = val_list[0]
                kw["Frau"]["2"] = val_list[1]
                kw["Frau"]["3"] = val_list[2]
            else:
                for item in val_list:
                    kw["Frau"]["1"].append(item)

            for i in range(len(val1['text'])):
                if df['text'][i] == "Stornierung":
                    kw["Frau"]["4"] = list(df[df['line'] == df['line'][i] + 1]['text'])[0]

        elif df['text'][index] == "Assekuradeur":
            val = df[df['left'] < df['left'][index - 1] - 50]
            val1 = val[val['top'] > df['top'][index] + 20]

            for i in range(len(df['text'])):
                if df['text'][i] == "Ansprechpartner":
                    val2 = val1[val1['top'] < df['top'][i]]
                    val_list = [" ".join(val2[val2['line'] == line]['text']) for line in
                                sorted(set(list(val2['line'])))]

                    if len(val_list) == 4:
                        kw["Frau"]["1"] = val_list[1]
                        kw["Frau"]["2"] = val_list[2]
                        kw["Frau"]["3"] = val_list[3]
                    else:
                        kw["Frau"]["1"] = val_list

        elif df['text'][index] == "Liebhaberfahrzeuge" and df['text'][index-1] == "für":
            kw["Frau"]["4"] = df['text'][index-2]

        elif df['text'][index] == "OCC-Beitragsrechnung" and not kw["Frau"]["4"]:
            kw["Frau"]["4"] = list(df[df['line'] == df['line'][index]+1]['text'])[0]

        if "Versicherungsschein" in re.sub('[\W_]+', '', df['text'][index]) and not kw["Versicherungsschein Nr"]:
            if "Nr" in re.sub('[\W_]+', '', df['text'][index]):
                kw["Versicherungsschein Nr"] = df['text'][index + 1]
            else:
                kw["Versicherungsschein Nr"] = df['text'][index + 2]

        elif df['text'][index] == "Ansprechpartner" and df['text'][index - 1] == "Ihr":
            kw["Ihr Ansprechpartner"] = ' '.join(list(df[df['line'] == df['line'][index] + 1]['text'])[-2:])

        elif df['text'][index] == "betreut" and df['text'][index - 1] == "Es":
            if not kw["Es betreut Sie"]:
                kw["Es betreut Sie"] = ' '.join(list(df[df['line'] == df['line'][index] + 1]['text'])[:2])

        elif df['text'][index] == "Vertragsbeginn" or "Beginn" in re.sub('[\W_]+', '', df['text'][index]):
            if not kw["Vertragsbeginn"] and len(df['text'][index + 1]):
                kw["Vertragsbeginn"] = df['text'][index + 1]

        elif df['text'][index] == "Vertragsablauf" or "Ablauf" in re.sub('[\W_]+', '', df['text'][index]):
            if not kw["Vertragsablauf"] and len(df['text'][index + 1]) > 1:
                kw["Vertragsablauf"] = df['text'][index + 1]

        elif "Zahlweise" in df['text'][index]:
            if df['left'][index + 3] > df['left'][index]:
                kw["Zahlweise"] = df['text'][index + 3]
            else:
                kw["Zahlweise"] = df['text'][index + 2]

        elif df['text'][index] == "Änderungsart":
            kw["Änderungsart"] = df['text'][index + 1]

        elif df['text'][index] == "Hersteller":
            if "Typ" in list(df[df['line'] == df['line'][index]]['text']):
                kw["Hersteller"] = df['text'][index + 1]

        elif df['text'][index] == "Typ":
            if "Hersteller" in list(df[df['line'] == df['line'][index]]['text']):
                kw["Typ"] = df['text'][index + 1]

        elif df['text'][index] == "Fahrzeugart":
            kw["Fahrzeugart"] = df['text'][index]

        elif df['text'][index] == "Kennzeichen" and df['text'][index - 1] == "Historische":
            for i in range(len(df['text'])):
                if df['text'][i] == "Erstzulassung":
                    kw["Historische Kennzeichen"] = ' '.join(list(df['text'][index + 1:i]))
                    kw["Erstzulassung"] = df['text'][i + 1]

        elif df['text'][index] == "Fahrgestellnummer":
            kw["Fahrgestellnummer"] = df['text'][index + 1]

        elif df['text'][index] == "Motorenstärke":
            kw["Motorenstärke"] = df['text'][index + 1]

        elif df['text'][index] == "Pauschalversicherungssumme" or "Pauschal" in df['text'][index]:
            kw["Pauschalversicherungssumme"] = ' '.join(list(df['text'][index + 1:index + 3]))

        elif df['text'][index] == "Person":
            kw["Deckung"] = ' '.join(list(df['text'][index + 1:index + 3]))

        elif df['text'][index].strip() == "Teilkasko":
            if "Haftpflicht" in list(df[df['line'] == df['line'][index] - 1]['text']) or "Haftpflicht" in list(
                    df[df['line'] == df['line'][index]]['text']):
                kw["Selbstbeteiligung"]["Teilkasko"].append(df['text'][index + 2])
            else:
                kw["Selbstbeteiligung"]["Teilkasko"].append(df['text'][index + 1])
                kw["Selbstbeteiligung"]["Teilkasko"].append(df['text'][index + 2])

        elif df['text'][index].strip() == "Haftpflicht":
            if "Teilkasko" in list(df[df['line'] == df['line'][index] + 1]['text']) or "Teilkasko" in list(
                    df[df['line'] == df['line'][index]]['text']):
                kw["Selbstbeteiligung"]["Teilkasko"].append(df['text'][index + 2])

    return kw


def find_values_occ(pdf_dir):
    """
    Finds values of given keywords in occ forms and pass the values to another function for converting to json.

    Arguments:
    pdf_dir -- string, path to the pdf files want to read.

    """

    excel_dir = os.path.join(pdf_dir, 'excel')

    for folder in os.listdir(excel_dir):

        kw = ret_kw_occ()[0]  # reset the dictionary

        for excel_file in os.listdir(os.path.join(excel_dir, folder)):
            excel = os.path.join(os.path.join(excel_dir, folder), excel_file)

            # convert excels to pandas dataframe
            df_raw = pd.read_excel(excel).drop(['Unnamed: 0'], axis=1)

            df_raw['text'] = df_raw['text'].apply(str)

            df_correct = word_similarity(df_raw, ret_kw_occ()[2])

            kw = first_page_occ(df_correct, kw)

        json_output(pdf_dir, kw, folder)
