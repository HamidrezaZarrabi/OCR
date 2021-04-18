# Import libraries
from utils.utils import json_output, verification
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import cv2
import re
import os


def preprocess_image(img):
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


def ret_ergo():
    """
    Defining custom keywords in function

    Return:
    keywords -- dictionary, contain all defined keywords
    verf_list -- list, contain page verification keywords
    diff_list -- list, contain important words to correct in case of mis recognizing
    """
    keywords = {"ERGO Kfz-Versicherung":[]
           ,"Versicherungsnehmer":{"1":[], "2":[], "3":[], "4":[]}
           ,"Versicherungs":[]
           ,"Tag der Änderung":[]
           ,"Ablauf der Versicherung":[]
           ,"Amtliches Kennzeichen":[]
           ,"Art und Verwendung":[]
           ,"Hersteller Typ":[]
           ,"Identifizierungs-Nummer":[]
           ,"Stärke":[]
           ,"zulässiges Gesamtgewicht":[]
           ,"Erstzulassung":[]
           ,"Kfz-Haftpflichtversicherung":[]
           ,"Selbstbeteiligung":{"Vollkasko":[]
                                ,"Teilkasko":[]}
           ,"Beitrag":{"Kfz-Haftpflichtversicherung":[]
                      ,"Schadensfreie Jahre 1":[]
                      ,"Kaskoversicherung":[]
                      ,"Schadensfreie Jahre 2":[]
                      ,"Kfz-Schutzbrief":[]
                      ,"Gesamtjahresbeitrag":[]
                      ,"Monatlich zu zahlender Beitrag":[]}
           ,"AKB":[]}

    verf_list = {'p1':["Identifizierungs-Nummer", "Hersteller", "Gesamtgewicht", "Ablauf"]
                , 'p2':["Vollkasko", "Teilkasko", "Kaskoversicherung", "Beitragssatz"]}

    diff_list = []

    return keywords, verf_list, diff_list


def first_page_ergo(df, kw):
    """
    Custom structures of the first page of ergo forms

    Arguments:
    df -- pandas dataframe, a dataframe which contain information of the first page
    kw -- dictionary, dictionary of keywords
    """

    # iterate over words in dataframe and find values
    for index in range(len(df['text'])):

        if df['text'][index] == "Versicherungsunternehmen":
            val = df[df['line'] == df.iloc[index]['line'] + 1]
            kw["Versicherungs"] = list(val[val['left'] > df.iloc[index]['left']]['text'])[0]
            val = df[df['left'] < df.iloc[index]['left'] - 10]
            kw["Versicherungsnehmer"]["1"] = " ".join(list(val[val['line'] == df.iloc[index]['line'] + 1]['text']))
            kw["Versicherungsnehmer"]["2"] = " ".join(list(val[val['line'] == df.iloc[index]['line'] + 2]['text']))
            kw["Versicherungsnehmer"]["3"] = " ".join(list(val[val['line'] == df.iloc[index]['line'] + 3]['text']))
            if list(val[val['line'] == df.iloc[index]['line'] + 4]['text'])[0] != "Vertragsdauer":
                kw["Versicherungsnehmer"]["4"] = " ".join(list(val[val['line'] == df.iloc[index]['line'] + 4]['text']))

        elif df['text'][index] == "Änderung" or df['text'][index] == "Anderung":
            kw["Tag der Änderung"] = df['text'][index + 1][:-1]

        elif df['text'][index] == "Beginn" and kw["Tag der Änderung"] == []:
            kw["Tag der Änderung"] = list(df[df['line'] == df.iloc[index]['line']]['text'])[-3][:-1]

        elif df['text'][index] == 'Versicherung' and df['text'][index - 1] == "der":
            kw["Ablauf der Versicherung"] = df['text'][index + 1][:-1]

        elif df['text'][index] == "Kennzeichen":
            kw["Amtliches Kennzeichen"] = " ".join(list(df[df['line'] == df.iloc[index]['line']]['text'])[2:])

        elif df['text'][index] == "Verwendung":
            kw["Art und Verwendung"] = re.sub("@G|@", "G",
                                              " ".join(list(df[df['line'] == df.iloc[index]['line']]['text'])[3:]))

        elif df['text'][index] == "Typ" and df['text'][index - 2] == "Hersteller":
            if "/" in " ".join(list(df[df['line'] == df.iloc[index]['line'] + 2]['text'])):
                kw["Hersteller Typ"] = list(df[df['line'] == df.iloc[index]['line'] + 2]['text'])[0]
            else:
                kw["Hersteller Typ"] = " ".join(list(df[df['line'] == df.iloc[index]['line']]['text'])[3:])

        elif df['text'][index] == "Identifizierungs-Nummer":
            kw["Identifizierungs-Nummer"] = df['text'][index + 1]

        elif df['text'][index] == "Stärke" or df['text'][index] == "Starke" or df['text'][
            index] == "Storke":
            kw["Stärke"] = list(df[df['line'] == df.iloc[index]['line']]['text'])[-1]

        elif df['text'][index] == "Gesamtgewicht":
            kw["zulässiges Gesamtgewicht"] = list(df[df['line'] == df.iloc[index]['line']]['text'])[-1]

        elif df['text'][index] == "Erstzulassung":
            kw["Erstzulassung"] = list(df[df['line'] == df.iloc[index]['line']]['text'])[-1]

        elif df['text'][index] == "pauschal":
            kw["Kfz-Haftpflichtversicherung"] = df['text'][index + 1]

    return kw


def second_page_ergo(df, kw):
    """
    Custom structures of the second page of ergo forms

    Arguments:
    df -- pandas dataframe, a dataframe which contain information of the first page
    kw -- dictionary, dictionary of keywords
    """

    # iterate over words in dataframe to find values
    for index in range(len(df['text'])):
        if df['text'][index] == "Kfz-Versicherung" and df['text'][index - 1] == "ERGO":
            val = df[df['left'] > df.iloc[index]['left']]
            kw["ERGO Kfz-Versicherung"] = re.sub('-.*', '',
                                                 "".join(list(val[val['line'] == df.iloc[index]['line']]['text'])))

        elif re.sub('[\W_]+', '', df['text'][index]) == "Selbstbeteiligung" and \
                list(df[df['line'] == df.iloc[index]['line']]['text'])[-1] == "Kaskoversicherung":
            kw["Selbstbeteiligung"]["Vollkasko"] = list(df[df['line'] == df.iloc[index]['line'] + 1]['text'])[-2]
            kw["Selbstbeteiligung"]["Teilkasko"] = list(df[df['line'] == df.iloc[index]['line'] + 2]['text'])[-2]

        elif re.sub('[\W_]+', '', df['text'][index]) == "Vollkasko" and kw["Selbstbeteiligung"]["Vollkasko"] == []:
            kw["Selbstbeteiligung"]["Vollkasko"] = df['text'][index + 1]

        elif re.sub('[\W_]+', '', df['text'][index]) == "Teilkasko" and kw["Selbstbeteiligung"]["Teilkasko"] == []:
            kw["Selbstbeteiligung"]["Teilkasko"] = df['text'][index + 1]

        elif re.sub('[\W_]+', '', df['text'][index]) == "Beitragssatz" and df['text'][index - 2] == "Jahre" and \
                kw["Beitrag"]["Schadensfreie Jahre 1"] == []:
            kw["Beitrag"]["Schadensfreie Jahre 1"] = df['text'][index - 1]
            kw["Beitrag"]["Kfz-Haftpflichtversicherung"] = list(df[df['line'] == df.iloc[index]['line'] + 1]['text'])[
                -2]

        elif re.sub('[\W_]+', '', df['text'][index]) == "Beitragssatz" and df['text'][index - 2] == "Jahre" and \
                kw["Beitrag"]["Schadensfreie Jahre 2"] == []:
            kw["Beitrag"]["Schadensfreie Jahre 2"] = df['text'][index - 1]
            kw["Beitrag"]["Kaskoversicherung"] = list(df[df['line'] == df.iloc[index]['line'] + 1]['text'])[-2]

        elif df['text'][index] == "Kfz-Schutzbrief":
            kw["Beitrag"]["Kfz-Schutzbrief"] = list(df[df['line'] == df.iloc[index]['line'] + 1]['text'])[-2]

        elif df['text'][index] == "Gesamtjahresbeitrag":
            kw["Beitrag"]["Gesamtjahresbeitrag"] = df['text'][index + 1]

        elif df['text'][index] == "zahlender" and df['text'][index + 1] == "Beitrag":
            kw["Beitrag"]["Monatlich zu zahlender Beitrag"] = list(df[df['line'] == df.iloc[index]['line']]['text'])[-2]

        elif df['text'][index] == "pauschal" and kw["Kfz-Haftpflichtversicherung"] == []:
            kw["Kfz-Haftpflichtversicherung"] = df['text'][index + 1]

        elif re.sub('[\W_]+', '', df['text'][index]) == "AKB":
            if re.sub('[\W_]+', '', df['text'][index + 1]) == "Spezial":
                kw["AKB"] = df['text'][index + 3][:-1]
            else:
                kw["AKB"] = df['text'][index + 2][:-1]

    return kw


def find_values_ergo(pdf_dir):
    """
    Finds values of given keywords in Ergo forms and pass the values to another function for converting to json.

    Arguments:
    pdf_dir -- string, path to the pdf files want to read.

    """

    excel_dir = os.path.join(pdf_dir, 'excel')

    for folder in os.listdir(excel_dir):

        kw = ret_ergo()[0]  # reset the dictionary

        for excel_file in os.listdir(os.path.join(excel_dir, folder)):

            excel = os.path.join(os.path.join(excel_dir, folder), excel_file)

            # convert excels to pandas dataframe
            df_raw = pd.read_excel(excel).drop(['Unnamed: 0'], axis=1)

            df = df_raw

            # Verify the page
            if verification(df['text'], ret_ergo()[1]['p1']):

                kw = first_page_ergo(df, kw)

            elif verification(df['text'], ret_ergo()[1]['p2']):

                kw = second_page_ergo(df, kw)

        json_output(pdf_dir, kw, folder)
