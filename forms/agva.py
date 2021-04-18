# Import libraries
from utils.utils import json_output, verification, remove_lines, word_similarity, manual_block, manual_line
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import cv2
import re
import os


def processing_image_agva(img_path):
    """
    Perform preprocessing tasks on image to remove noises with openCV.

    Arguments:
    img -- string, path of an image which want to perform preprocessing on it.

    Return:
    image -- numpy array, array of output image which performed preprocessing tasks on it.

    """

    image = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)  # Convert RGB image to grayscale

    if image is None:
        image = plt.imread(img_path)  # Cv2 might not read the image so read it with plt
        image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)  # Convert the plt image to grayscale

    image = remove_lines(image, horizontal=True, vertical=True, thick=1)

    image = cv2.medianBlur(image, 1)  # Remove noises in the image with median blur
    # Setting all background pixels to 0 and foreground pixels to 255
    image = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    image = cv2.dilate(image, np.ones((1, 1), np.uint8), iterations=1)  # Dilation
    image = cv2.erode(image, np.ones((1, 1), np.uint8), iterations=2)  # Erosion
    image = cv2.morphologyEx(image, cv2.MORPH_OPEN, np.ones((1, 1), np.uint8))

    return image


def ret_agva():
    """
    Defining custom keywords in function

    Return:
    keywords -- dictionary, contain all defined keywords
    verf_list -- list, contain page verification keywords
    diff_list -- list, contain important words to correct in case of mis recognizing
    """

    keywords = {}

    verf_list = {"p1": ["Versicherungsorte", "Betriebsstelle", "Versicherungsnehmer", "Vertragsdauer"]
        , "p2": ["Sachsubstanzschäden", "Unterbrechungsschäden", "Höchstentschädigung", "Selbstbeteiligung"]
        , "p3": ["Beitragsberechnung", "Bedingungen", "Beitragssatz", "Mindestbeitrag"]
        , "p5": ["Versichertes", "Unternehmen", "Versicherer", "Gerichtsstand"]}

    diff_list = ["Versicherungsschein-Nummer", "Versicherungsnehmer", "Vertragsdauer", "Versicherungsmakler"
        , "Deklaration", "Höchstentschädigung", "Selbstbeteiligung", "Sachsubstanzschäden", "Führender"
        , "Unterbrechungsschäden", "Erdbeben", "Leitungswasser", "Fahrzeuganprall", "Überschwemmung", "Schneedruck"
        , "Vulkanausbruch", "Einbruchdiebstahl", "Kunstgegenstände", "Kostenpositionen", "Unternehmen"
        , "Versicherungsorte", "Beteiligungsverhältnisse", "Beitragsberechnung", "Bedingungen", "Erdsenkung"
        , "Gerichtsstand", "Betriebsstelle", "Versicherungsgegenstand", "Beitragssatz", "Mindestbeitrag"
        , "Gefahren", "Beteiligungsverhältnisse"]

    return keywords, verf_list, diff_list


def first_page(df, kw):
    """
    Custom structures of the first page of agva forms

    Arguments:
    df -- pandas dataframe, a dataframe which contain information of the first page
    kw -- dictionary, dictionary of keywords

    Return:
    kw -- dictionary, contain keywords and values of first page
    """

    for index in range(len(df['text'])):

        if df['text'][index] == "Versicherungsschein-Nummer" and "Versicherungsschein-Nummer" not in kw:
            if df['text'][index+1] in list(df[df['line'] == df['line'][index]]['text']):
                kw["Versicherungsschein-Nummer"] = ' '.join(manual_line(df['top'][index], df, dist=20))
            else:
                kw["Versicherungsschein-Nummer"] = ''

        elif df['text'][index] == "Versicherungsnehmer" and "Versicherungsnehmer" not in kw:
            kw["Versicherungsnehmer"] = df['text'][index + 1] + ' ' + df['text'][index + 2]

        elif df['text'][index] == "Vertragsdauer" and "Vertragsdauer" not in kw:
            kw["Vertragsdauer"] = {"1": df['text'][index + 1],
                                   "2": manual_line(df['top'][index], df)[-1]}

        elif re.sub('[\W_]+', '', df['text'][index]) == "Versicherer" and df['text'][index - 1] == "Führender":
            try:
                kw["Führender Versicherer"] = ' '.join(manual_line(df['top'][index], df)[2:])
            except IndexError:
                pass

        elif df['text'][index] == "Versicherungsmakler" and "Versicherungsmakler" not in kw:
            kw["Versicherungsmakler"] = ' '.join(manual_line(df['top'][index], df)[1:])

    return kw


def second_page(df, kw):
    """
    Custom structures of the second page of agva forms

    Arguments:
    df -- pandas dataframe, a dataframe which contain information of the third page
    kw -- dictionary, dictionary of keywords

    Return:
    kw -- dictionary, contain keywords and values of second page
    """

    hoc = 0
    selb = 0
    part1 = 0
    part2 = 0

    if "Deklaration" in kw:
        jj = ' 1'
        kw["Deklaration" + f"{jj}"] = {}
    else:
        jj = ''
        kw["Deklaration" + f"{jj}"] = {}

    for index in range(len(df['text'])):

        if df['text'][index] == "Höchstentschädigung" and "Selbstbeteiligung" in list(
                df[df['line'] == df['line'][index]]['text']):
            right_hoc = df['left'][index] + df['width'][index]
            left_hoc = df['left'][index]
            top_hoc = df['top'][index]

        elif df['text'][index] == "Selbstbeteiligung" and "Höchstentschädigung" in list(
                df[df['line'] == df['line'][index]]['text']):
            left_selb = df['left'][index]
            right_selb = df['left'][index] + df['width'][index]
            top_selb = df['top'][index]

        elif re.sub('[\W_]+', '', df['text'][index]) == "Sachsubstanzschäden" and "Höchstentschädigung" in list(
                df[df['line'] == df['line'][index] - 1]['text']):

            down = df[df['top'] > df['top'][index] + 10]
            for i in range(len(df['text'])):

                if re.sub('[\W_]+', '', df['text'][i]) == "Unterbrechungsschäden" and df['text'][i] in list(
                        df[df['line'] == df['line'][i]]['text'])[:2]:
                    part1 = down[down['top'] < df['top'][i] - 10]
                    val = df[df['line'] > df['line'][i] + 1]
                    part2 = val[val['top'] > df['top'][i] + 10]

    try:
        middle_num = abs(int((right_hoc - left_selb) / 2))
        middle = left_selb - middle_num
        h_val = df[df['left'] > (left_hoc - middle_num) + 20]
        h_val1 = h_val[h_val['left'] < middle]
        hoc = h_val1[h_val1['top'] > top_hoc + 10]
        s_val = df[df['left'] > middle]
        s_val1 = s_val[s_val['left'] < (right_selb + middle_num) + 20]
        selb = s_val1[s_val1['top'] > top_selb + 10]
    except:
        pass

    if int not in [type(part1), type(hoc), type(selb)]:

        kw["Deklaration" + f"{jj}"]["Sachsubstanzschäden"] = {}

        for index in range(len(part1['text'])):

            if re.sub('[\W_]+', '', part1.iloc[index]['text']) == "Brand":
                kw["Deklaration" + f"{jj}"]["Sachsubstanzschäden"]["Brand"] = \
                    [' '.join(list(hoc[hoc['line'] == part1.iloc[index]['line']]['text']))
                        , ' '.join(list(selb[selb['line'] == part1.iloc[index]['line']]['text']))]

            elif part1.iloc[index]['text'] == "Innere" and re.sub('[\W_]+', '',
                                                                  part1.iloc[index + 1]['text']) == "Unruhen":
                kw["Deklaration" + f"{jj}"]["Sachsubstanzschäden"]["Innere Unruhen"] = \
                    [' '.join(list(hoc[hoc['line'] == part1.iloc[index]['line']]['text']))
                        , ' '.join(list(selb[selb['line'] == part1.iloc[index]['line']]['text']))]
                if len(kw["Deklaration" + f"{jj}"]["Sachsubstanzschäden"]["Innere Unruhen"][0]) <= 1:
                    kw["Deklaration" + f"{jj}"]["Sachsubstanzschäden"]["Innere Unruhen"] = \
                        [' '.join(list(hoc[hoc['line'] == part1.iloc[index]['line'] + 1]['text']))
                            , ' '.join(list(selb[selb['line'] == part1.iloc[index]['line'] + 1]['text']))]

            elif part1.iloc[index]['text'] == "Fahrzeuganprall":
                kw["Deklaration" + f"{jj}"]["Sachsubstanzschäden"]["Fahrzeuganprall"] = \
                    [' '.join(list(hoc[hoc['line'] == part1.iloc[index]['line']]['text']))
                        , ' '.join(list(selb[selb['line'] == part1.iloc[index]['line']]['text']))]

            elif part1.iloc[index]['text'] == "Leitungswasser":
                kw["Deklaration" + f"{jj}"]["Sachsubstanzschäden"]["Leitungswasser"] = \
                    [' '.join(list(hoc[hoc['line'] == part1.iloc[index]['line']]['text']))
                        , ' '.join(list(selb[selb['line'] == part1.iloc[index]['line']]['text']))]

            elif re.sub('[\W_]+', '', part1.iloc[index]['text']) == "Sturm" and part1.iloc[index + 1][
                'text'] == "Hagel":
                kw["Deklaration" + f"{jj}"]["Sachsubstanzschäden"]["Sturm"] = \
                    [' '.join(list(hoc[hoc['line'] == part1.iloc[index]['line']]['text']))
                        , ' '.join(list(selb[selb['line'] == part1.iloc[index]['line']]['text']))]

            elif part1.iloc[index]['text'] == "Erdbeben":
                kw["Deklaration" + f"{jj}"]["Sachsubstanzschäden"]["Erdbeben"] = \
                    [' '.join(list(hoc[hoc['line'] == part1.iloc[index]['line']]['text']))
                        , ' '.join(list(selb[selb['line'] == part1.iloc[index]['line']]['text']))]

            elif part1.iloc[index]['text'] == "Überschwemmung":
                kw["Deklaration" + f"{jj}"]["Sachsubstanzschäden"]["Überschwemmung"] = \
                    [' '.join(list(hoc[hoc['line'] == part1.iloc[index]['line']]['text']))
                        , ' '.join(list(selb[selb['line'] == part1.iloc[index]['line']]['text']))]

            elif part1.iloc[index]['text'] == "Erdsenkung":
                kw["Deklaration" + f"{jj}"]["Sachsubstanzschäden"]["Erdsenkung"] = \
                    [' '.join(list(hoc[hoc['line'] == part1.iloc[index]['line']]['text']))
                        , ' '.join(list(selb[selb['line'] == part1.iloc[index]['line']]['text']))]

            elif part1.iloc[index]['text'] == "Schneedruck":
                kw["Deklaration" + f"{jj}"]["Sachsubstanzschäden"]["Schneedruck"] = \
                    [' '.join(list(hoc[hoc['line'] == part1.iloc[index]['line']]['text']))
                        , ' '.join(list(selb[selb['line'] == part1.iloc[index]['line']]['text']))]

            elif part1.iloc[index]['text'] == "Vulkanausbruch":
                kw["Deklaration" + f"{jj}"]["Sachsubstanzschäden"]["Vulkanausbruch"] = \
                    [' '.join(list(hoc[hoc['line'] == part1.iloc[index]['line']]['text']))
                        , ' '.join(list(selb[selb['line'] == part1.iloc[index]['line']]['text']))]

            elif part1.iloc[index]['text'] == "Einbruchdiebstahl" and "Vandalismus" in list(
                    part1[part1['line'] == part1.iloc[index]['line']]['text']):
                kw["Deklaration" + f"{jj}"]["Sachsubstanzschäden"]["Einbruchdiebstahl"] = \
                    [' '.join(list(hoc[hoc['line'] == part1.iloc[index]['line']]['text']))
                        , ' '.join(list(selb[selb['line'] == part1.iloc[index]['line']]['text']))]
                if len(kw["Deklaration" + f"{jj}"]["Sachsubstanzschäden"]["Einbruchdiebstahl"][0]) <= 1:
                    kw["Deklaration" + f"{jj}"]["Sachsubstanzschäden"]["Einbruchdiebstahl"] = \
                        [' '.join(list(hoc[hoc['line'] == part1.iloc[index]['line'] + 1]['text']))
                            , ' '.join(list(selb[selb['line'] == part1.iloc[index]['line'] + 1]['text']))]

            elif part1.iloc[index]['text'] == "Sachsubstanzschäden":
                kw["Deklaration" + f"{jj}"]["Sachsubstanzschäden"]["Sonstige Sachsubstanzschäden"] = \
                    [' '.join(list(hoc[hoc['line'] == part1.iloc[index]['line']]['text']))
                        , ' '.join(list(selb[selb['line'] == part1.iloc[index]['line']]['text']))]

            elif part1.iloc[index]['text'] == "Transportwegen":
                kw["Deklaration" + f"{jj}"]["Sachsubstanzschäden"]["Schäden auf Transportwegen"] = \
                    [' '.join(list(hoc[hoc['line'] == part1.iloc[index]['line']]['text']))
                        , ' '.join(list(selb[selb['line'] == part1.iloc[index]['line']]['text']))]

            elif part1.iloc[index]['text'] == "elektronischen" and part1.iloc[index + 1]['text'] == "Geräten":
                kw["Deklaration" + f"{jj}"]["Sachsubstanzschäden"]["Schäden an elektronischen Geräten"] = \
                    [' '.join(list(hoc[hoc['line'] == part1.iloc[index]['line']]['text']))
                        , ' '.join(list(selb[selb['line'] == part1.iloc[index]['line']]['text']))]
                if len(kw["Deklaration" + f"{jj}"]["Sachsubstanzschäden"]["Schäden an elektronischen Geräten"][0]) <= 1:
                    kw["Deklaration" + f"{jj}"]["Sachsubstanzschäden"]["Schäden an elektronischen Geräten"] = \
                        [' '.join(list(hoc[hoc['line'] == part1.iloc[index]['line'] + 1]['text']))
                            , ' '.join(list(selb[selb['line'] == part1.iloc[index]['line'] + 1]['text']))]

            elif part1.iloc[index]['text'] == "Elektronikschäden" and "eingesetzten" in list(
                    part1[part1['line'] == part1.iloc[index]['line']]['text']):
                kw["Deklaration" + f"{jj}"]["Sachsubstanzschäden"]["Elektronikschäden an mobil eingesetzten Geräte"] = \
                    [' '.join(list(hoc[hoc['line'] == part1.iloc[index]['line']]['text']))
                        , ' '.join(list(selb[selb['line'] == part1.iloc[index]['line']]['text']))]
                if len(kw["Deklaration" + f"{jj}"]["Sachsubstanzschäden"][
                           "Elektronikschäden an mobil eingesetzten Geräte"][0]) <= 1:
                    kw["Deklaration" + f"{jj}"]["Sachsubstanzschäden"][
                        "Elektronikschäden an mobil eingesetzten Geräte"] = \
                        [' '.join(list(hoc[hoc['line'] == part1.iloc[index]['line'] + 1]['text']))
                            , ' '.join(list(selb[selb['line'] == part1.iloc[index]['line'] + 1]['text']))]

            elif part1.iloc[index]['text'] == "Softwareklausel":
                kw["Deklaration" + f"{jj}"]["Sachsubstanzschäden"]["Softwareklausel"] = \
                    [' '.join(list(hoc[hoc['line'] == part1.iloc[index]['line']]['text']))
                        , ' '.join(list(selb[selb['line'] == part1.iloc[index]['line']]['text']))]

            elif part1.iloc[index]['text'] == "Schäden" and "Maschinen" in list(
                    part1[part1['line'] == part1.iloc[index]['line']]['text']):
                kw["Deklaration" + f"{jj}"]["Sachsubstanzschäden"]["Schäden an Maschinen"] = \
                    [' '.join(list(hoc[hoc['line'] == part1.iloc[index]['line']]['text']))
                        , ' '.join(list(selb[selb['line'] == part1.iloc[index]['line']]['text']))]

            elif part1.iloc[index]['text'] == "Schäden" and "Montagen" in list(
                    part1[part1['line'] == part1.iloc[index]['line']]['text']):
                kw["Deklaration" + f"{jj}"]["Sachsubstanzschäden"]["Schäden bei Montagen"] = \
                    [' '.join(list(hoc[hoc['line'] == part1.iloc[index]['line']]['text']))
                        , ' '.join(list(selb[selb['line'] == part1.iloc[index]['line']]['text']))]

            elif part1.iloc[index]['text'] == "Kunstgegenstände":
                kw["Deklaration" + f"{jj}"]["Sachsubstanzschäden"]["Kunstgegenstände"] = \
                    [' '.join(list(hoc[hoc['line'] == part1.iloc[index]['line']]['text']))
                        , ' '.join(list(selb[selb['line'] == part1.iloc[index]['line']]['text']))]

    if int not in [type(part2), type(hoc), type(selb)]:

        kw["Deklaration" + f"{jj}"]["Unterbrechungsschäden"] = {}

        for index in range(len(part2['text'])):

            for i in range(len(df['text'])):

                if re.sub('[\W_]+', '', df.iloc[i]['text']) == "Haftzeit":
                    kw["Deklaration" + f"{jj}"]["Unterbrechungsschäden"]["Haftzeit"] = df.iloc[i + 1]['text']

            if re.sub('[\W_]+', '', part2.iloc[index]['text']) == "Brand" and re.sub(
                    '[\W_]+', '', part2.iloc[index + 1]['text']) == "Blitzschlag":
                kw["Deklaration" + f"{jj}"]["Unterbrechungsschäden"]["Brand"] = \
                    [' '.join(list(hoc[hoc['line'] == part2.iloc[index]['line']]['text']))
                        , ' '.join(list(selb[selb['line'] == part2.iloc[index]['line']]['text']))]

            elif part2.iloc[index]['text'] == "Innere" and re.sub('[\W_]+', '',
                                                                  part2.iloc[index + 1]['text']) == "Unruhen":
                kw["Deklaration" + f"{jj}"]["Unterbrechungsschäden"]["Innere Unruhen"] = \
                    [' '.join(list(hoc[hoc['line'] == part2.iloc[index]['line']]['text']))
                        , ' '.join(list(selb[selb['line'] == part2.iloc[index]['line']]['text']))]
                if len(kw["Deklaration" + f"{jj}"]["Unterbrechungsschäden"]["Innere Unruhen"][0]) <= 1:
                    kw["Deklaration" + f"{jj}"]["Unterbrechungsschäden"]["Innere Unruhen"] = \
                        [' '.join(list(hoc[hoc['line'] == part2.iloc[index]['line'] + 1]['text']))
                            , ' '.join(list(selb[selb['line'] == part2.iloc[index]['line'] + 1]['text']))]

            elif re.sub('[\W_]+', '', part2.iloc[index]['text']) == "Fahrzeuganprall":
                kw["Deklaration" + f"{jj}"]["Unterbrechungsschäden"]["Fahrzeuganprall"] = \
                    [' '.join(list(hoc[hoc['line'] == part2.iloc[index]['line']]['text']))
                        , ' '.join(list(selb[selb['line'] == part2.iloc[index]['line']]['text']))]

            elif re.sub('[\W_]+', '', part2.iloc[index]['text']) == "Leitungswasser":
                kw["Deklaration" + f"{jj}"]["Unterbrechungsschäden"]["Leitungswasser"] = \
                    [' '.join(list(hoc[hoc['line'] == part2.iloc[index]['line']]['text']))
                        , ' '.join(list(selb[selb['line'] == part2.iloc[index]['line']]['text']))]

            elif re.sub('[\W_]+', '', part2.iloc[index]['text']) == "Sturm" and part2.iloc[index + 1][
                'text'] == "Hagel":
                kw["Deklaration" + f"{jj}"]["Unterbrechungsschäden"]["Sturm"] = \
                    [' '.join(list(hoc[hoc['line'] == part2.iloc[index]['line']]['text']))
                        , ' '.join(list(selb[selb['line'] == part2.iloc[index]['line']]['text']))]

            elif re.sub('[\W_]+', '', part2.iloc[index]['text']) == "Erdbeben":
                kw["Deklaration" + f"{jj}"]["Unterbrechungsschäden"]["Erdbeben"] = \
                    [' '.join(list(hoc[hoc['line'] == part2.iloc[index]['line']]['text']))
                        , ' '.join(list(selb[selb['line'] == part2.iloc[index]['line']]['text']))]

            elif re.sub('[\W_]+', '', part2.iloc[index]['text']) == "Überschwemmung":
                kw["Deklaration" + f"{jj}"]["Unterbrechungsschäden"]["Überschwemmung"] = \
                    [' '.join(list(hoc[hoc['line'] == part2.iloc[index]['line']]['text']))
                        , ' '.join(list(selb[selb['line'] == part2.iloc[index]['line']]['text']))]

            elif re.sub('[\W_]+', '', part2.iloc[index]['text']) == "Erdsenkung":
                kw["Deklaration" + f"{jj}"]["Unterbrechungsschäden"]["Erdsenkung"] = \
                    [' '.join(list(hoc[hoc['line'] == part2.iloc[index]['line']]['text']))
                        , ' '.join(list(selb[selb['line'] == part2.iloc[index]['line']]['text']))]

            elif re.sub('[\W_]+', '', part2.iloc[index]['text']) == "Schneedruck":
                kw["Deklaration" + f"{jj}"]["Unterbrechungsschäden"]["Schneedruck"] = \
                    [' '.join(list(hoc[hoc['line'] == part2.iloc[index]['line']]['text']))
                        , ' '.join(list(selb[selb['line'] == part2.iloc[index]['line']]['text']))]

            elif re.sub('[\W_]+', '', part2.iloc[index]['text']) == "Vulkanausbruch":
                kw["Deklaration" + f"{jj}"]["Unterbrechungsschäden"]["Vulkanausbruch"] = \
                    [' '.join(list(hoc[hoc['line'] == part2.iloc[index]['line']]['text']))
                        , ' '.join(list(selb[selb['line'] == part2.iloc[index]['line']]['text']))]

            elif re.sub('[\W_]+', '', part2.iloc[index]['text']) == "Einbruchdiebstahl" and "Vandalismus" in list(
                    part2[part2['line'] == part2.iloc[index]['line']]['text']):
                kw["Deklaration" + f"{jj}"]["Unterbrechungsschäden"]["Einbruchdiebstahl"] = \
                    [' '.join(list(hoc[hoc['line'] == part2.iloc[index]['line']]['text']))
                        , ' '.join(list(selb[selb['line'] == part2.iloc[index]['line']]['text']))]
                if len(kw["Deklaration" + f"{jj}"]["Unterbrechungsschäden"]["Einbruchdiebstahl"][0]) <= 1:
                    kw["Deklaration" + f"{jj}"]["Unterbrechungsschäden"]["Einbruchdiebstahl"] = \
                        [' '.join(list(hoc[hoc['line'] == part2.iloc[index]['line'] + 1]['text']))
                            , ' '.join(list(selb[selb['line'] == part2.iloc[index]['line'] + 1]['text']))]

            elif re.sub('[\W_]+', '', part2.iloc[index]['text']) == "Sachsubstanzschäden" and part2.iloc[index - 1][
                'text'] == "Sonstige":
                kw["Deklaration" + f"{jj}"]["Unterbrechungsschäden"]["Sonstige Sachsubstanzschäden"] = \
                    [' '.join(list(hoc[hoc['line'] == part2.iloc[index]['line']]['text']))
                        , ' '.join(list(selb[selb['line'] == part2.iloc[index]['line']]['text']))]

            elif re.sub('[\W_]+', '', part2.iloc[index]['text']) == "elektronischen" and part2.iloc[index + 1][
                'text'] == "Geräten":
                kw["Deklaration" + f"{jj}"]["Unterbrechungsschäden"]["Schäden an elektronischen Geräten"] = \
                    [' '.join(list(hoc[hoc['line'] == part2.iloc[index]['line']]['text']))
                        , ' '.join(list(selb[selb['line'] == part2.iloc[index]['line']]['text']))]
                if len(kw["Deklaration" + f"{jj}"]["Unterbrechungsschäden"]["Schäden an elektronischen Geräten"][
                           0]) <= 1:
                    kw["Deklaration" + f"{jj}"]["Unterbrechungsschäden"]["Schäden an elektronischen Geräten"] = \
                        [' '.join(list(hoc[hoc['line'] == part2.iloc[index]['line'] + 1]['text']))
                            , ' '.join(list(selb[selb['line'] == part2.iloc[index]['line'] + 1]['text']))]

            elif re.sub('[\W_]+', '', part2.iloc[index]['text']) == "Schäden" and "Maschinen" in list(
                    part2[part2['line'] == part2.iloc[index]['line']]['text']):
                kw["Deklaration" + f"{jj}"]["Unterbrechungsschäden"]["Schäden an Maschinen"] = \
                    [' '.join(list(hoc[hoc['line'] == part2.iloc[index]['line']]['text']))
                        , ' '.join(list(selb[selb['line'] == part2.iloc[index]['line']]['text']))]

            elif re.sub('[\W_]+', '', part2.iloc[index]['text']) == "Schäden" and "Montagen" in list(
                    part2[part2['line'] == part2.iloc[index]['line']]['text']):
                kw["Deklaration" + f"{jj}"]["Unterbrechungsschäden"]["Schäden bei Montagen"] = \
                    [' '.join(list(hoc[hoc['line'] == part2.iloc[index]['line']]['text']))
                        , ' '.join(list(selb[selb['line'] == part2.iloc[index]['line']]['text']))]

    return kw


def third_page(df, kw):
    """
    Update keywords in third page

    Arguments:
    df -- pandas dataframe, a dataframe which contain information of the third page
    kw -- dictionary, dictionary of keywords

    Return:
    kw -- dictionary, contain keywords and values of first page
    """

    for index in range(len(df['text'])):

        if df['text'][index] == "Beitragsberechnung":

            kw["Beitragsberechnung"] = {}

            for i in range(len(df['text'])):

                if re.sub('[\W_]+', '', df['text'][i]) == "Umsatz":
                    kw["Beitragsberechnung"]["Umsatz"] = ' '.join(manual_line(df['top'][i], df)[1:])

                elif re.sub('[\W_]+', '', df['text'][i]) == "Beitragssatz":
                    kw["Beitragsberechnung"]["Beitragssatz"] = ' '.join(
                        manual_line(df['top'][i], df)[1:])

                elif re.sub('[\W_]+', '', df['text'][i]) == "Jahresbeitrag":
                    kw["Beitragsberechnung"]["Jahresbeitrag"] = ' '.join(
                        manual_line(df['top'][i], df)[1:])

                elif re.sub('[\W_]+', '', df['text'][i]) == "Mindestbeitrag" and "Vertraglicher" in list(
                        df[df['line'] == df['line'][i]]['text']):
                    kw["Beitragsberechnung"]["Vertraglicher Mindestbeitrag"] = ' '.join(
                        manual_line(df['top'][i], df)[2:])

                elif re.sub('[\W_]+', '', df['text'][i]) == "Bedingungen" and "Industriepolice" in list(
                        df[df['line'] == df['line'][i]]['text']):
                    kw["Beitragsberechnung"]["Es gelten die Bedingungen zur ARTUS Industriepolice (AGVA) Fassung"] = \
                        manual_line(df['top'][i], df)[-1]

    return kw


def forth_page(df, kw, inpage):
    """
    Custom structures of the third page of agva forms

    Arguments:
    df -- pandas dataframe, a dataframe which contain information of the second page
    kw -- dictionary, dictionary of keywords
    inpage -- boolean, True or False to know Beteiligungsverhältnisse is in page or not

    Return:
    kw -- dictionary, contain keywords and values of second page
    """

    for index in range(len(df['text'])):

        if df['text'][index] == "Unternehmen" and "Weitere" in list(df[df['line'] == df['line'][index]]['text']):
            kw["Weitere vers. Unternehmen"] = {}

            val = df[df['left'] > df['left'][index]]
            val1 = val[val['top'] > df['top'][index] - 10]

            for i in range(len(df['text'])):

                if df['text'][i] == "Versicherungsorte" and "Betriebsstelle" in list(df.loc[i:i + 5, 'text']):
                    val2 = val1[val1['top'] < df['top'][i]]
                    val_list = manual_block(val2)

                    for j in range(1, len(val_list) + 1):
                        kw["Weitere vers. Unternehmen"][f"{j}"] = ' '.join(val_list[j - 1])

        elif df['text'][index] == "Versicherungsorte" and "Betriebsstelle" in list(df.loc[index:index + 5, 'text']):
            kw["Versicherungsorte Betriebsstelle"] = {}

            val = df[df['left'] > df['left'][index] + 150]
            val1 = val[val['top'] > df['top'][index]]
            val2 = val1[val1['left'] < df['left'][index] + 1250]
            if inpage:
                for j in range(len(df)):
                    if df['text'][j] == "Beteiligungsverhältnisse":
                        val3 = val2[val2['top'] < df['top'][j] - 10]
                        val_list = manual_block(val3)

                        tre = df[df['top'] > df['top'][j] + 10]
                        tree = tre[tre['top'] < df['top'][j] + 500]
                        treee = manual_block(tree)
                        kw["Beteiligungsverhältnisse"] = {}
                        for item in range(1, len(treee) + 1):
                            kw["Beteiligungsverhältnisse"][f"{item}"] = ' '.join(treee[item - 1])

            else:
                val_list = manual_block(val2)

            for line in range(1, len(val_list) + 1):
                try:
                    kw["Versicherungsorte Betriebsstelle"][f"{line}"] = ' '.join(val_list[line - 1])
                except IndexError:
                    pass

    return kw


def fifth_page(df, kw):
    """
    Custom structures of the fifth page of agva forms

    Arguments:
    df -- pandas dataframe, a dataframe which contain information of the fifth page
    kw -- dictionary, dictionary of keywords

    Return:
    kw -- dictionary, contain keywords and values of second page
    """

    left_list = []
    right_list = []
    left_temp = []
    right_temp = []

    # Extract words under Versicherer as left_temp and under Versichertes Unternehmen as right_temp
    for index in range(len(df['text'])):

        if df['text'][index] == "Versicherer" and "Unternehmen" in list(df[df['line'] == df['line'][index]]['text']):
            val = df[df['top'] > df['top'][index] + 9]
            val1 = val[val['left'] < df['left'][index] + df['width'][index] + 10]
            right_temp = val1[val1['left'] > df['left'][index] - 10]
            left_temp = val1[val1['left'] < df['left'][index] - 150]

    if type(left_temp) is not list and type(right_temp) is not list:
        for index in (right_temp.index):
            if len(right_temp.loc[index]['text']) < 2:
                right_temp = right_temp.drop([index])
        right_temp = right_temp.reset_index()

        for index in range(len(right_temp)):

            tre = left_temp[left_temp['top'] > right_temp.iloc[index]['top'] - 10]

            if index == right_temp.last_valid_index():
                tree = tre[tre['top'] < right_temp.iloc[index]['top'] + 200]
            else:
                tree = tre[tre['top'] < right_temp.iloc[index + 1]['top'] - 10]

            left_list.append(' '.join(list(tree['text'])))
            right_list.append(right_temp.iloc[index]['text'])

    if len(left_list) == len(right_list) and len(left_list) > 0:

        kw["Verzeichnis der versicherten Unternehmen"] = {}
        kw["Verzeichnis der versicherten Unternehmen"]["Versichertes Unternehmen"] = {}
        kw["Verzeichnis der versicherten Unternehmen"]["Versicherer"] = {}

        for block in range(1, len(left_list) + 1):
            kw["Verzeichnis der versicherten Unternehmen"]["Versichertes Unternehmen"][f"{block}"] = left_list[
                block - 1]
            kw["Verzeichnis der versicherten Unternehmen"]["Versicherer"][f"{block}"] = right_list[block - 1]

    return kw


def find_values_agva(pdf_dir):
    """
    Finds values of given keywords in occ forms and pass the values to another function for converting to json.

    Arguments:
    pdf_dir -- string, path to the pdf files want to read.

    """

    inpage = []

    excel_dir = os.path.join(pdf_dir, 'excel')

    for folder in sorted(os.listdir(excel_dir)):

        kw = ret_agva()[0]  # reset the keywords dictionary

        for excel_file in sorted(os.listdir(os.path.join(excel_dir, folder))):

            excel = os.path.join(os.path.join(excel_dir, folder), excel_file)

            # convert excels to pandas dataframe
            df_raw = pd.read_excel(excel).drop(['Unnamed: 0'], axis=1)

            df_raw['text'] = df_raw['text'].apply(str)  # convert all texts to str format

            df_correct = word_similarity(df_raw, ret_agva()[2])  # correct the Unrecognized words

            # verify each page
            if verification(list(df_correct['text']), ret_agva()[1]['p1']) or inpage == False:

                if inpage == False:

                    for index in range(len(df_correct['text'])):

                        if df_correct['text'][index] == "Beteiligungsverhältnisse" and df_correct['text'][index] == \
                                list(
                                    df_correct[df_correct['line'] == df_correct['line'][index]]['text'])[0]:
                            val = df_correct[df_correct['left'] > df_correct['left'][index] + 150]
                            val1 = val[val['top'] < df_correct['top'][index] + 10]
                            val2 = val1[val1['left'] < df_correct['left'][index] + 1000]
                            val_list = manual_block(val2)

                            for line in range(1, len(val_list) + 1):
                                try:
                                    a = list(kw["Versicherungsorte Betriebsstelle"].keys())[-1]
                                    kw["Versicherungsorte Betriebsstelle"][f"{line + int(a)}"] = ' '.join(
                                        val_list[line - 1])
                                except IndexError:
                                    pass

                            tre = df_correct[df_correct['top'] > df_correct['top'][index] + 10]
                            tree = tre[tre['top'] < df_correct['top'][index] + 500]
                            treee = manual_block(tree)
                            kw["Beteiligungsverhältnisse"] = {}
                            for item in range(1, len(treee) + 1):
                                kw["Beteiligungsverhältnisse"][f"{item}"] = ' '.join(treee[item - 1])
                            inpage = []

                else:
                    if "Versicherungsschein-Nummer" in list(
                            df_correct['text']) and "Versicherungsgegenstand" not in list(
                            df_correct['text']):
                        kw = first_page(df_correct, kw)
                        pass
                    else:
                        if "Beteiligungsverhältnisse" in list(df_correct['text']):
                            inpage = True
                            kw = forth_page(df_correct, kw, inpage)
                        else:
                            inpage = False
                            kw = forth_page(df_correct, kw, inpage)

            elif verification(list(df_correct['text']), ret_agva()[1]['p2']):

                for i in range(len(df_correct['text'])):

                    if df_correct['text'][i] == "Versicherte" and df_correct['text'][i + 1] == "Gefahren":
                        kw = second_page(df_correct, kw)

            elif verification(list(df_correct['text']), ret_agva()[1]['p3']):

                kw = third_page(df_correct, kw)

            elif verification(list(df_correct['text']), ret_agva()[1]['p5']):

                for i in range(len(df_correct['text'])):
                    if df_correct['text'][i] == "Versichertes" and df_correct['text'][i + 1] == "Unternehmen":
                        kw = fifth_page(df_correct, kw)

            elif "Kostenpositionen" in list(df_correct['text']) and "Sachsubstanzschäden" in list(df_correct['text']):

                for index in range(len(df_correct['text'])):

                    if df_correct['text'][index] == "Kostenpositionen":
                        val = df_correct[df_correct['line'] == df_correct['line'][index] + 2]
                        kw["Kostenpositionen"] = list(val['text'])[-1]

            elif "Beteiligungsverhältnisse" in list(df_correct['text']):

                for index in range(len(df_correct['text'])):

                    if df_correct['text'][index] == "Beteiligungsverhältnisse" and df_correct['text'][index] == list(
                            df_correct[df_correct['line'] == df_correct['line'][index]]['text'])[0]:
                        kw["Beteiligungsverhältnisse"] = {}
                        kw["Beteiligungsverhältnisse"]["1"] = ' '.join(
                            list(df_correct[df_correct['line'] == df_correct['line'][index] + 1]['text']))
                        kw["Beteiligungsverhältnisse"]["2"] = ' '.join(
                            list(df_correct[df_correct['line'] == df_correct['line'][index] + 2]['text']))

        # convert the kw dictionary to json file
        json_output(pdf_dir, kw, folder)
