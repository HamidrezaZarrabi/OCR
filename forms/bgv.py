# Import libraries
from utils.utils import verification, json_output
from utils.my_functions import word_similarity
import pandas as pd
import numpy as np
import cv2
import re
import os


def preprocess_image(img):
    """
    Perform preprocessing tasks on bgv image to remove noises with openCV.

    Arguments:
    img -- string, path of an image which want to perform preprocessing on it.

    Return:
    image -- numpy array, array of output image which performed preprocessing tasks on it.

    """
    image = cv2.imread(img, cv2.IMREAD_GRAYSCALE)  # Convert RGB image to grayscale

    if image is None:
        image = plt.imread(img)  # Cv2 might not read the image so read it with plt
        image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)  # Convert the plt image to grayscale

    # Setting all background pixels to 0 and foreground pixels to 255
    image = cv2.threshold(image, 105, 255, cv2.THRESH_BINARY)[1]
    image = cv2.dilate(image, np.ones((1, 1), np.uint8), iterations=1)  # Dilation
    image = cv2.erode(image, np.ones((1, 1), np.uint8), iterations=2)  # Erodsion
    image = cv2.morphologyEx(image, cv2.MORPH_OPEN, np.ones((1, 1), np.uint8))

    return image


def ret_kw_bgv():
    """
    Defining custom keywords in function

    Return:
    keywords -- dictionary, contain all defined keywords
    verf_list -- list, contain page verification keywords
    diff_list -- list, contain important words to correct in case of mis recognizing
    """
    keywords = {"Ihr Ansprechpartner": []
        , "KFZ-Versicherung": []
        , "Versicherungsbeginn": []
        , "Versicherungsablauf": []
        , "Versichertes Fahrzeug": []
        , "Fahrzeugart": []
        , "Fahrzg-Ident-Nr": []
        , "Hersteller": []
        , "Stärke": []
        , "Erstzulassung": []
        , "Herst Nr./Typ Nr.": []
        , "Versicherungsumfang": {"KFZ-Haftpflichtversicherung": []
            , "Jahresbeitrag 1": []
            , "KFZ-Vollkaskoversicherung": []
            , "Jahresbeitrag 2": []}
        , "Beitragsrechnung": {"von": []
            , "bis": []
            , "Gesamt": []}}

    verf_kw_bgv = {"p1": ["Ansprechpartner", "Fahrzeugart", "Erstzulassung", "Versicherungsablauf"]}

    diff_list = ["Ansprechpartner"
        , "KFZ-Versicherung"
        , "Versicherungsbeginn"
        , "Versicherungsablauf"
        , "Versichertes Fahrzeug"
        , "Fahrzeugart"
        , "Fahrzg-Ident-Nr"
        , "Hersteller"
        , "Stärke"
        , "Erstzulassung"
        , "Versicherungsumfang"
        , "KFZ-Haftpflichtversicherung"
        , "Jahresbeitrag"
        , "KFZ-Vollkaskoversicherung"
        , "Beitragsrechnung"
        , "Gesamt"]

    return keywords, verf_kw_bgv, diff_list


def first_page_bgv(df, kw):
    """
    Custom structures of the first page of pgv forms

    Arguments:
    df -- pandas dataframe, a dataframe which contain information of the first page
    kw -- dictionary, dictionary of keywords
    """

    permission = True

    # Iterate over texts in dataframe and with the defined structure for each keyword, extract the output value
    for index in range(len(df['text'])):

        if df['text'][index] == "Ansprechpartner" and df['text'][index - 1] == "Ihr":
            kw["Ihr Ansprechpartner"] = ' '.join(list(df[df['line'] == df['line'][index] + 1]['text'])[-2:])

        elif df['text'][index] == "Fahrzeug":
            if df['text'][index - 1] == "für" or df['text'][index - 1] == "tür" or df['text'][index - 1] == "fur":
                kw["Versichertes Fahrzeug"] = df['text'][index + 1] + ' ' + df['text'][index + 2]

        elif df['text'][index] == "Versicherungsbeginn" or "beginn" in df['text'][index]:
            kw["Versicherungsbeginn"] = df['text'][index + 1]

        elif df['text'][index] == "Versicherungsablauf" or "ablauf" in df['text'][index]:
            kw["Versicherungsablauf"] = df['text'][index + 1]

        elif re.sub('[\W_]+', '', df['text'][index]) == "Fahrzeug" and re.sub('[\W_]+', '',
                                                                              df['text'][index - 1]) == "Versichertes":
            if not kw["Versichertes Fahrzeug"]:
                kw["Versichertes Fahrzeug"] = df['text'][index + 1] + ' ' + df['text'][index + 2]

        elif df['text'][index] == "Fahrzeugart":
            if "KH" not in list(df[df['line'] == df['line'][index]]['text']) or "KV" not in list(
                    df[df['line'] == df['line'][index]]['text']):
                kw["Fahrzeugart"] = ' '.join(list(df[df['line'] == df['line'][index]]['text'])[1:])
            else:
                permission = False
                kw["Fahrzeugart"] = df['text'][index + 1]

        elif "IdentNr" in re.sub('[\W_]+', '', df['text'][index]):
            if permission:
                val = df[df['line'] == df['line'][index]]
                val1 = val[val['left'] > df['left'][index]]
                kw["Fahrzg-Ident-Nr"] = re.sub('[\W_]+', '', ''.join(list(val1['text'])))
            else:
                kw["Fahrzg-Ident-Nr"] = df['text'][index + 1]

        elif df['text'][index] == "Hersteller":
            if permission:
                kw["Hersteller"] = ' '.join(list(df[df['line'] == df['line'][index]]['text'])[1:])
            else:
                kw["Hersteller"] = df['text'][index + 1] + ' ' + df['text'][index + 2]

        elif df['text'][index] == "Stärke":
            kw["Stärke"] = df['text'][index + 1] + ' ' + df['text'][index + 2]

        elif df['text'][index] == "Erstzulassung" and not kw["Erstzulassung"]:
            kw["Erstzulassung"] = df['text'][index + 1]

        elif "HerstNr" in re.sub('[\W_]+', '', df['text'][index]):
            if permission:
                kw["Herst Nr./Typ Nr."] = ''.join(list(df[df['line'] == df['line'][index]]['text'])[-1])
            else:
                kw["Herst Nr./Typ Nr."] = df['text'][index + 2]

        elif re.sub('[\W_]+', '', df['text'][index]) == "KFZHaftpflichtversicherung" or "KFZHaftp" in re.sub('[\W_]+',
                                                                                                             '',
                                                                                                             df['text'][
                                                                                                                 index]):

            val = df[df['line'] >= df['line'][index] + 1]
            val1 = val[val['line'] <= df['line'][index] + 2]
            val_list = list(val1['text'])
            kw["Versicherungsumfang"]["KFZ-Haftpflichtversicherung"] = ' '.join(val_list)

            if re.sub('[\W_]+', '', df['text'][index + 1]) == "KH":
                if len(df['text'][index + 3]) > 2:
                    kw["Versicherungsumfang"]["Jahresbeitrag 1"] = df['text'][index + 3]
                else:
                    kw["Versicherungsumfang"]["Jahresbeitrag 1"] = df['text'][index + 4]
            else:
                if len(df['text'][index + 2]) > 2:
                    kw["Versicherungsumfang"]["Jahresbeitrag 1"] = df['text'][index + 2]
                else:
                    kw["Versicherungsumfang"]["Jahresbeitrag 1"] = df['text'][index + 3]

        elif re.sub('[\W_]+', '', df['text'][index]) == "KFZ-Vollkaskoversicherung" or "KFZVollkas" in re.sub('[\W_]+',
                                                                                                              '', df[
                                                                                                                  'text'][
                                                                                                                  index]):

            val = df[df['line'] >= df['line'][index] + 1]
            val1 = val[val['line'] <= df['line'][index] + 2]
            val_list = list(val1['text'])
            kw["Versicherungsumfang"]["KFZ-Vollkaskoversicherung"] = ' '.join(val_list)

            if re.sub('[\W_]+', '', df['text'][index + 1]) == "KV":
                kw["Versicherungsumfang"]["Jahresbeitrag 2"] = df['text'][index + 3]
            else:
                kw["Versicherungsumfang"]["Jahresbeitrag 2"] = df['text'][index + 2]

        elif df['text'][index] == "Beitragsrechnung":
            if re.sub('[\W_]+', '', df['text'][index + 1]) == "von" or re.sub('[\W_]+', '',
                                                                              df['text'][index + 2]) == "bis" or re.sub(
                '[\W_]+', '', df['text'][index + 2]) == "von":
                val1 = list(df[df['line'] == df['line'][index] + 1]['text'])
            elif "EUR" in list(df[df['line'] == df['line'][index] + 1]['text']):
                val1 = list(df[df['line'] == df['line'][index] + 1]['text'])

            try:
                kw["Beitragsrechnung"]["von"] = val1[1]
                kw["Beitragsrechnung"]["bis"] = val1[2]
                kw["Beitragsrechnung"]["Gesamt"] = ' '.join(val1[-2:])
            except:
                pass

    return kw


def find_values_bgv(pdf_dir):
    """
    Finds values of given keywords in pgv forms and pass the values to another function for converting to json.

    Arguments:
    pdf_dir -- string, path to the pdf files.

    """

    excel_dir = os.path.join(pdf_dir, 'excel')

    # Iterate over excel files to read
    for folder in os.listdir(excel_dir):

        kw = ret_kw_bgv()[0]  # reset the dictionary

        for excel_file in os.listdir(os.path.join(excel_dir, folder)):

            # Read the full path of the excel file
            excel = os.path.join(os.path.join(excel_dir, folder), excel_file)

            # Convert excels to pandas dataframe
            df_correct = pd.read_excel(excel).drop(['Unnamed: 0'], axis=1)

            df_correct['text'] = df_correct['text'].apply(str)

            df_correct = word_similarity(df_correct, ret_kw_bgv()[2])

            # Verify the page
            if verification(df_correct['text'], ret_kw_bgv()[1]['p1']):

                # Remove texts with lower specific amount of x
                try:
                    index_word = list(df_correct['text']).index("Versicherungsumfang")
                    df = df_correct[df_correct['left'] > df_correct.iloc[index_word]['left'] - 20].reset_index()
                    if len(df) == 0:
                        index_word = list(df_correct['text']).index("Beitragsrechnung".strip("\."))
                        df = df_correct[df_correct['left'] > df_correct.iloc[index_word]['left'] - 20].reset_index()
                except:
                    df = df_correct

                # Extract the values from the first page
                kw = first_page_bgv(df, kw)

        # pass the extracted data to another function for converting to json
        json_output(pdf_dir, kw, folder)
