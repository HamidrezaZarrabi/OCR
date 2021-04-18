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


def ret_kw_wurtt():
    """
    Defining custom keywords in function

    Return:
    keywords -- dictionary, contain all defined keywords
    verf_list -- list, contain page verification keywords
    diff_list -- list, contain important words to correct in case of mis recognizings
    """
    keywords = {"Versicherungsnehmer": {"1": [], "2": [], "3": [], "4": [], "5": []}
        , "Es betreut Sie": []
        , "Versicherungsschein-Nr": []
        , "Fahrzeug": []
        , "Amtliches Kennzeichen": []
        , "Modellbezeichnung": []
        , "Hersteller/Typ-Nummer": []
        , "Fahrzeug-Ident.- Nummer": []
        , "Modell": []
        , "Nennleistung": []
        , "Baujahr": []
        , "Zulässige Gesamtmasse": []
        , "Erstzulassung": []
        , "Versicherung": []
            ################
        , "Versicherungssumme": []
        , "Schutzbrief 1": []
        , "Fahrzeugvollversicherung 1": {"Selbstbeteiligung": []}
        , "Fahrzeugteilversicherung": {"Selbstbeteiligung": []}
        , "AKB": []
            ################
        , "Zahlungsperiode": []
        , "Versicherungsperiode": []
        , "bis": []
        , "Kfz-Haftpflichtversicherung": {"Jahresbeitrag": []
            , "Ihr Beitrag": []}
        , "Schutzbrief 2": {"Jahresbeitrag": []
            , "Ihr Beitrag": []}
        , "Fahrzeugvollversicherung 2": {"Jahresbeitrag": []
            , "Ihr Beitrag": []}
        , "zuzüglich Versicherungsteuer zahlender Betrag für den Berechnungszeitraum": []}

    verf_list = {"p1": ["betreut", "Versicherungsnehmer", "Amtliches", "Kennzeichen"]
        , "p2": ["Selbstbeteiligung", "Fahrzeugteilversicherung", "Versicherungssumme", "Fahrzeug"]
        , "p3": ["zuzüglich", "Zahlungsperiode", "Versicherungsperiode", "Berechnungszeitraum"]}

    diff_list = []

    return keywords, verf_list, diff_list


def first_page_wurtt(df, kw):
    """
    Custom structures of the first page of Württ forms

    Arguments:
    df -- pandas dataframe, a dataframe which contain information of the first page
    kw -- dictionary, dictionary of keywords
    """

    df['text'] = df['text'].apply(str)

    # Iterate over texts in dataframe and with the defined structure for each keyword, extract the output value
    for index in range(len(df['text'])):

        if df['text'][index] == "betreut" and df['text'][index - 1] == "Es":
            val = df[df['left'] > df['left'][index - 1] - 15]
            kw["Es betreut Sie"] = " ".join(list(val[val['line'] == df['line'][index] + 1]['text']))

        elif df['text'][index] == "Versicherungsnehmer" or "erungsnehmer" in df['text'][index]:
            val = df[df['left'] < df['left'][index] + df['width'][index] + 120]
            val1 = val[val['line'] > df['line'][index]]
            val2 = val1[val1['line'] < df['line'][index] + 10]
            val_list = [" ".join(val2[val2['line'] == line]['text']) for line in sorted(set(list(val2['line'])))]
            if len(val_list) <= 3:
                try:
                    kw["Versicherungsnehmer"]["1"] = val_list[0]
                    kw["Versicherungsnehmer"]["2"] = val_list[1]
                    kw["Versicherungsnehmer"]["3"] = val_list[2]
                except:
                    pass
            elif len(val_list) == 5:
                try:
                    kw["Versicherungsnehmer"]["1"] = val_list[0]
                    kw["Versicherungsnehmer"]["2"] = val_list[1]
                    kw["Versicherungsnehmer"]["3"] = val_list[2]
                    kw["Versicherungsnehmer"]["4"] = val_list[3] + " " + val_list[4]
                except:
                    pass
            else:
                try:
                    kw["Versicherungsnehmer"]["1"] = val_list[0]
                    kw["Versicherungsnehmer"]["2"] = val_list[1]
                    kw["Versicherungsnehmer"]["3"] = val_list[2]
                    kw["Versicherungsnehmer"]["4"] = val_list[3]
                except:
                    pass


        elif re.sub('[\W_]+', '', df['text'][index]) == "VersicherungsscheinNr":
            if kw["Versicherungsschein-Nr"] == []:
                kw["Versicherungsnehmer"]["5"] = list(df[df['line'] == df['line'][index] - 1]['text'])[-1]
                kw["Versicherungsschein-Nr"] = re.sub('.*KFZ', '', " ".join(
                    list(df[df['line'] == df['line'][index]]['text']))).strip()

        elif df['text'][index] == "Nachtrag" and kw["Versicherungsnehmer"]["5"] == []:
            kw["Versicherungsnehmer"]["5"] = list(df[df['line'] == df['line'][index] - 1]['text'])[-1]

        elif df['text'][index] == 'Kennzeichen' and df['text'][index - 1] == "Amtliches":
            kw["Amtliches Kennzeichen"] = " ".join(list(df[df['line'] == df['line'][index]]['text'])[2:])
            if "Oldtimer" not in list(df['text']):
                kw["Fahrzeug"] = list(df[df['line'] == df['line'][index] - 2]['text'])[-1]
            else:
                kw["Fahrzeug"] = list(df[df['line'] == df['line'][index] - 1]['text'])[-1]

        elif df['text'][index] == "Modellbezeichnung" or df['text'][index] == "Modellibezeichnung":
            kw["Modellbezeichnung"] = " ".join(list(df[df['line'] == df['line'][index]]['text'])[1:])

        elif re.sub('[\W_]+', '', re.sub('.*/', '', df['text'][index])) == "TypNummer":
            val = df[df['line'] == df['line'][index]]
            kw["Hersteller/Typ-Nummer"] = " ".join(list(val[val['left'] > df['left'][index]]['text']))

        elif df['text'][index] == "Modell":
            kw["Modell"] = " ".join(list(df[df['line'] == df['line'][index]]['text'])[1:])

        elif re.sub('[\W_]+', '', df['text'][index]) == "Nummer":
            kw["Fahrzeug-Ident.- Nummer"] = df['text'][index + 1]

        elif df['text'][index] == "Nennleistung":
            kw["Nennleistung"] = " ".join(list(df[df['line'] == df['line'][index]]['text'])[1:])

            if kw["Fahrzeug-Ident.- Nummer"] == []:
                kw["Fahrzeug-Ident.- Nummer"] = list(df[df['line'] == df['line'][index] - 1]['text'])[-1]

        elif df['text'][index] == "Baujahr":
            kw["Baujahr"] = df['text'][index + 1]

        elif df['text'][index] == "Gesamtmasse":
            kw["Zulässige Gesamtmasse"] = df['text'][index + 1]


        elif df['text'][index] == "Erstzulassung":
            kw["Erstzulassung"] = " ".join(list(df[df['line'] == df['line'][index]]['text'])[1:])

        if df['text'][index] == "Versicherung" and df['text'][index + 1] == "AG":
            kw["Versicherung"] = list(df[df['line'] == df['line'][index] - 1]['text'])[0]

            if len(kw["Versicherung"]) <= 4:
                try:
                    kw["Versicherung"] = list(df[df['line'] == df['line'][index] - 2]['text'])[0]
                except:
                    pass

    return kw


def second_page_wurtt(df, kw):
    """
    Custom structures of the second page of Württ forms

    Arguments:
    df -- pandas dataframe, a dataframe which contain information of the first page
    kw -- dictionary, dictionary of keywords
    """

    df['text'] = df['text'].apply(str)

    for index in range(len(df['text'])):

        if re.sub('[\W_]+', '', df['text'][index]) == "VersicherungsscheinNr" and kw["Versicherungsschein-Nr"] == []:
            kw["Versicherungsschein-Nr"] = list(df[df['line'] == df['line'][index]]['text'])[-1]

        elif df['text'][index] == "Versicherungssumme" and df['text'][index + 1] == "beträgt":
            list_line = list(df[df['line'] == df['line'][index]]['text'])
            kw["Versicherungssumme"] = list_line[list_line.index("EUR") + 1] + " " + list_line[
                list_line.index("EUR") + 2].strip("\. | \,")

        elif df['text'][index] == "Schutzbrief":
            kw["Schutzbrief 1"] = re.sub('[\W_]+', '', df['text'][index + 1])

        elif df['text'][index] == "Fahrzeugvollversicherung" and kw["Fahrzeugvollversicherung 1"][
            "Selbstbeteiligung"] == []:
            if "EUR" in list(df[df['line'] == df['line'][index] + 1]['text']):
                list_line = list(df[df['line'] == df['line'][index] + 1]['text'])
                try:
                    kw["Fahrzeugvollversicherung 1"]["Selbstbeteiligung"] = list_line[list_line.index("EUR") + 1].strip(
                        "\.")
                except:
                    pass
                list_line = list(df[df['line'] == df['line'][index] + 3]['text'])
                try:
                    kw["Fahrzeugteilversicherung"]["Selbstbeteiligung"] = list_line[list_line.index("EUR") + 1].strip(
                        "\.")
                except:
                    pass

        elif df['text'][index] == "Fahrzeugteilversicherung" and kw["Fahrzeugteilversicherung"][
            "Selbstbeteiligung"] == []:
            list_line = list(df[df['line'] == df['line'][index] + 1]['text'])
            kw["Fahrzeugteilversicherung"]["Selbstbeteiligung"] = list_line[2]


        elif re.sub('C', '', re.sub('[\W_]+', '', df['text'][index])) == "AKB" and df['text'][index + 1] == "Stand":
            kw["AKB"] = df['text'][index + 2]

    return kw


def third_page_wurtt(df, kw):
    """
    Custome structures of the third page of Württ forms

    Arguments:
    df -- pandas dataframe, a dataframe which contain information of the first page
    kw -- dictionary, dictionary of keywords
    """

    df['text'] = df['text'].apply(str)

    for index in range(len(df['text'])):

        if re.sub('[\W_]+', '', df['text'][index]) == "VersicherungsscheinNr" and kw["Versicherungsschein-Nr"] == []:
            if df['text'][index + 2] == "KFZ":
                kw["Versicherungsschein-Nr"] = df['text'][index + 3]
            else:
                kw["Versicherungsschein-Nr"] = df['text'][index + 2]

        elif df['text'][index] == "Zahlungsperiode" and df['text'][index - 1] == "Vereinbarte":
            if len(df['text'][index + 1]) <= 2:
                kw["Zahlungsperiode"] = df['text'][index + 2]
            else:
                kw["Zahlungsperiode"] = df['text'][index + 1]

        elif df['text'][index] == "Versicherungsperiode":
            if len(df['text'][index + 1]) <= 2:
                kw["Versicherungsperiode"] = df['text'][index + 2]
                kw["bis"] = df['text'][index + 4]
            else:
                kw["Versicherungsperiode"] = df['text'][index + 1]
                kw["bis"] = df['text'][index + 3]

        elif "ahresbeitr" in df['text'][index]:
            if df['text'][index + 1] == "Ihr" or df['text'][index + 2] == "Ihr" or "Jahresbeitrag" in list(
                    df[df['line'] == df['line'][index] - 1]['text']):
                val = df[df['left'] < df['left'][index] + df['width'][index] + 10]
                val1 = val[val['left'] > df['left'][index]]
                val2 = val1[val1['top'] > df['top'][index]]
                for i in range(len(df['text'])):
                    if df['text'][i] == "zuziiglich" or df['text'][i] == "zuzüglich" or df['text'][i] == "zuzuglich":
                        val3 = val2[val2['top'] < df['top'][i]]['text']
                        list_val = list(val3)

                        if len(list_val) == 3:

                            kw["Kfz-Haftpflichtversicherung"]["Jahresbeitrag"] = list_val[0]
                            kw["Schutzbrief 2"]["Jahresbeitrag"] = list_val[1]
                            kw["Fahrzeugvollversicherung 2"]["Jahresbeitrag"] = list_val[2]
                        elif len(list_val) == 2:

                            kw["Kfz-Haftpflichtversicherung"]["Jahresbeitrag"] = list_val[0]
                            kw["Fahrzeugvollversicherung 2"]["Jahresbeitrag"] = list_val[1]

                        else:
                            kw["Kfz-Haftpflichtversicherung"]["Jahresbeitrag"] = list_val[0] + list_val[1]
                            kw["Schutzbrief 2"]["Jahresbeitrag"] = list_val[2]
                            kw["Fahrzeugvollversicherung 2"]["Jahresbeitrag"] = list_val[3]

        elif re.sub('[\W_]+', '', df['text'][index]) == "KfzHaftpflichtversicherung" and \
                kw["Kfz-Haftpflichtversicherung"]["Ihr Beitrag"] == []:
            if "Fahrzeugvollversicherung" not in (df['text'][index + 1], df['text'][index + 2]):
                kw["Kfz-Haftpflichtversicherung"]["Ihr Beitrag"] = df['text'][index + 1]

        elif df['text'][index] == "Fahrzeugvollversicherung" and kw["Fahrzeugvollversicherung 2"]["Ihr Beitrag"] == []:
            if "Kfz-Haftpflichtversicherung" not in (df['text'][index - 1], df['text'][index - 2]):
                kw["Fahrzeugvollversicherung 2"]["Ihr Beitrag"] = df['text'][index + 1]

        elif df['text'][index] == "Fahrzeugteilversicherung" and kw["Fahrzeugvollversicherung 2"]["Ihr Beitrag"] == []:
            kw["Fahrzeugvollversicherung 2"]["Ihr Beitrag"] = df['text'][index + 1]

        elif df['text'][index] == "Schutzbrief" and kw["Schutzbrief 2"]["Ihr Beitrag"] == []:
            kw["Schutzbrief 2"]["Ihr Beitrag"] = df['text'][index + 2]

        elif df['text'][index] == "Berechnungszeitraum":
            kw["zuzüglich Versicherungsteuer zahlender Betrag für den Berechnungszeitraum"] = df['text'][index + 1]

        elif df['text'][index] == "Versicherung" and df['text'][index + 1] == "AG":
            kw["Versicherung"] = df['text'][index - 1]

    return kw


def find_values_wurtt(pdf_dir):
    """
    Finds values of given keywords in württ forms and pass the values to another function for converting to json.

    Arguments:
    pdf_dir -- string, path to the pdf files.

    """

    excel_dir = os.path.join(pdf_dir, 'excel')

    # Iterate over excel files to read
    for folder in os.listdir(excel_dir):

        kw = ret_kw_wurtt()[0]  # reset the dictionary

        for excel_file in os.listdir(os.path.join(excel_dir, folder)):

            # Read the full path of the excel file
            excel = os.path.join(os.path.join(excel_dir, folder), excel_file)

            # Convert excels to pandas dataframe
            df_correct = pd.read_excel(excel).drop(['Unnamed: 0'], axis=1)

            # Verify the page
            if verification(df_correct['text'], ret_kw_wurtt()[1]['p1']):

                # Remove texts with lower specific amount of x
                try:
                    index_word = list(df_correct['text']).index("Versicherungsnehmer")
                    df = df_correct[df_correct['left'] > df_correct.iloc[index_word]['left'] - 20].reset_index()
                    if len(df) == 0:
                        index_word = list(df_correct['text']).index("Versicherungsschein-Nr".strip("\."))
                        df = df_correct[df_correct['left'] > df_correct.iloc[index_word]['left'] - 20].reset_index()
                except:
                    df = df_correct

                # Extract the values from the first page
                kw = first_page_wurtt(df, kw)

            # verify the page
            elif verification(df_correct['text'], ret_kw_wurtt()[1]['p2']):

                df = df_correct

                # Extract the values from the second page
                kw = second_page_wurtt(df, kw)

            # Verify the page
            elif verification(df_correct['text'], ret_kw_wurtt()[1]['p3']):

                try:
                    index_word = list(df_correct['text']).index("Beitragsberechnung", -1)
                    df = df_correct[df_correct['left'] > df_correct.iloc[index_word]['left'] - 20].reset_index()
                    if len(df) == 0:
                        index_word = list(df_correct['text']).index("Vereinbarte")
                        df = df_correct[df_correct['left'] > df_correct.iloc[index_word]['left'] - 20].reset_index()
                except:
                    df = df_correct

                # Extract the values from the first page
                kw = third_page_wurtt(df, kw)

        # pass the extracted data to another function for converting to json
        json_output(pdf_dir, kw, folder)
