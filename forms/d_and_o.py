from cv2 import cv2
import pandas as pd
import numpy as np
import re
import tr
import os

from utils.ms_lines import find_lines
from utils.constants import kw_d_and_o


def create_tr_df(image):
    """
    Create tr dataframe
    """
    cv2.imwrite('./1.jpeg', image)
    data = tr.run('./1.jpeg')
    os.remove('./1.jpeg')
    a = np.array(data)
    b1 = a[:, 0].tolist()
    b2 = a[:, 1:].tolist()
    c = [a + b for a, b in zip(b1, b2)]

    df_tr = pd.DataFrame.from_records(c, columns=['left', 'top', 'width', 'height', 'angle', 'text', 'conf'])
    df_tr = df_tr[['text', 'left', 'top', 'width', 'height', 'conf']]

    df_tr = find_lines(df_tr)
    df_tr = df_tr[df_tr['text'].astype(bool)].reset_index()
    df_tr = df_tr.drop(['index'], axis=1)

    return df_tr


def fill_name(block_df):
    """
    Fill keyword dictionary with name and address.

    Args:
        block_df: pandas dataframe, contain block data.

    Returns:
        kw1: dictionary, dictionary filled with name and address.
    """

    kw1 = {}

    plz_df = block_df[block_df['text'].str.contains('^\d{5}$')]

    try:
        kw1['VN PLZ'] = list(plz_df['text'])[-1]
    except IndexError:
        kw1['VN PLZ'] = 'NO_VALUE!'

    try:
        line_text = ' '.join(list(block_df[block_df['line'] == list(plz_df['line'])[-1]]['text']))
        kw1['VN Ort'] = line_text.split(list(plz_df['text'])[-1])[-1]
    except IndexError:
        kw1['VN Ort'] = 'NO_VALUE!'

    try:
        kw1['VN Str'] = ' '.join(list(block_df[block_df['line'] == max(list(block_df['line'])) - 1]['text']))
    except IndexError:
        kw1['VN Str'] = 'NO_VALUE!'

    try:
        name = ' '.join(list(block_df[block_df['line'] < list(plz_df['line'])[-1] - 1]['text']))
        re_list = ['.*Versicherungsnehmer/in', '.*:', '.*Firma', '.*Versicherungsnehmer', '.*\.com', '.*wird']
        for item in re_list:
            name = re.sub(item, '', name)
        kw1['VN Name'] = name.strip()
    except IndexError:
        kw1['VN Name'] = 'NO_VALUE!'

    return kw1


def name_and_address(df):
    """
    Find values for name and address of policy holder.

    Args:
        df: Pandas DataFrame, dataframe contain page information.

    Returns:
        kw1: dictionary, contain name and address and postal code and city.
    """

    kw1 = {}

    df = df[df['l-r'] == 0].reset_index()

    block_list = list(set(df['block']))

    for block in range(len(block_list)):
        block_df = df[df['block'] == block_list[block]]
        perv_block = df[df['block'] == block_list[block - 1]]

        if len(block_df[block_df['text'].str.contains('^\d{5}$')]) > 0 and \
                (len(block_df[block_df['text'].str.contains('Versicherungsnehmer')]) > 0 or
                 len(perv_block[perv_block['text'].str.contains('Versicherungsnehmer')]) > 0):

            if len(set(list(block_df['line']))) == 1:
                block_df = find_lines(block_df)
                kw1 = fill_name(block_df)
                return kw1

            else:
                kw1 = fill_name(block_df)
                return kw1

    return kw1


def policy_period(df):
    """
    Find values for policy period.
    """
    kw = {}

    lines = list(set(df['line']))

    for line in lines:
        line_df = df[df['line'] == line].reset_index()

        if len(line_df[line_df['text'].str.contains('Beginn')]) > 0:
            try:
                kw['gültig ab'] = list(line_df[line_df['text'].str.contains('\d{2}\.\d{2}\.\d{4}')]['text'])[0]
            except IndexError:
                pass

        elif len(line_df[line_df['text'].str.contains('Ablauf')]) > 0:
            try:
                kw['Ablaufdatum'] = list(line_df[line_df['text'].str.contains('\d{2}\.\d{2}\.\d{4}')]['text'])[0]
            except IndexError:
                pass

    return kw


def policy_number(df):
    """
    Extract policy number
    """
    kw = {}

    lines = list(set(df['line']))

    for i in range(len(lines)):
        line_df = df[df['line'] == lines[i]]
        perv_line_df = df[df['line'] == lines[i - 1]]

        if len(perv_line_df[perv_line_df['text'].str.contains('Versicherungsschein-Nr')]) > 0:
            try:
                kw['Policen_ID'] = list(line_df[line_df['text'].str.contains('\w+\d{3,}')]['text'])[0]
                return kw
            except IndexError:
                continue

    return kw


def policy_total(df):
    """
    Extract total assumption
    """
    kw = {}

    lines = list(set(df['line']))

    for i in range(len(lines)):
        line_df = df[df['line'] == lines[i]]
        perv_line_df = df[df['line'] == lines[i - 1]]

        if len(perv_line_df[perv_line_df['text'].str.contains('Versicherungssumme')]) > 0:
            try:
                kw['Versicherungssumme'] = list(line_df[line_df['text'].str.contains('\d{3}\.\d{3}')]['text'])[0]
                return kw
            except IndexError:
                continue

    return kw


def policy_prame(df):
    """
    Extract prame value.
    """
    kw = {}

    lines = list(set(df['line']))

    for i in range(len(lines)):
        line_df = df[df['line'] == lines[i]]

        if len(line_df[line_df['text'].str.contains('Versicherungsprämie')]) > 0 and \
                len(line_df[line_df['text'].str.contains('zuzüglich')]) > 0:
            try:
                kw['JNP'] = list(line_df[line_df['text'].str.contains('\d{1,3}\,\d+')]['text'])[0]
                return kw
            except IndexError:
                pass
        else:
            pass

    return kw


def policy_year(df):
    """
    Extract year of the policy
    """
    kw = {}

    block_list = list(set(df['block']))

    for block in range(len(block_list)):
        block_df = df[df['block'] == block_list[block]]

        if len(block_df[block_df['text'].str.contains('Allgemeinen')]) > 0 and \
                len(block_df[block_df['text'].str.contains('Bedingungen')]) > 0:
            index = list(block_df.index[block_df['text'].str.contains('Allgemeinen')])[0]
            block_df = block_df.loc[index:]
            val = list(block_df[(block_df['text'].str.contains('\(', regex=True)) |
                                (block_df['text'].str.contains('\)', regex=True))]['text'].index)
            val_ = ' '.join(list(block_df.loc[val[0]:val[-1]]['text']))
            kw['AVB'] = re.sub('[^\sA-Za-z-0-9_-]', '', val_)
            return kw

    return kw


def policy_aus(df):
    """
    Extract Ausfertigungsgrund
    """
    kw = {}

    lines = list(set(df['line']))

    for i in range(len(lines)):
        line_df = df[df['line'] == lines[i]]
        perv_line_df = df[df['line'] == lines[i - 1]]

        if len(perv_line_df[perv_line_df['text'].str.contains('Ausfertigungsgrund')]) > 0:
            try:
                kw['Änderungsgrund'] = ' '.join(list(line_df['text']))
                return kw
            except IndexError:
                continue

    return kw


def policy_name(df):
    """
    Extract Name
    """
    kw = {}

    lines = list(set(df['line']))

    for i in range(len(lines)):
        line_df = df[df['line'] == lines[i]]
        perv_line_df = df[df['line'] == lines[i - 1]]

        if len(perv_line_df[perv_line_df['text'].str.contains('Personen')]) > 0 and \
                len(perv_line_df[perv_line_df['text'].str.contains('versicherte$')]) > 0:
            try:
                kw['Mitversichert'] = ' '.join(list(line_df['text']))
                return kw
            except IndexError:
                continue

    return kw


def policy_risko(image):
    """
    Extract percents
    """
    kw = {}

    df_tr = create_tr_df(image)

    try:
        header = list(df_tr[df_tr['text'].str.contains('Beteiligte Versicherer')]['line'])[0]
        lines = list(df_tr[df_tr['text'].str.contains('%')]['line'])
        _ = lines[0]
    except IndexError:
        return kw

    kw['Beteiligte_Versicherer'] = []
    kw['Beteiligter_%'] = []

    for i in lines:
        line_text = df_tr[df_tr['line'] == i]
        text = ' '.join(list(line_text[~line_text['text'].str.contains('%', regex=True)]['text']))
        percent = ' '.join(list(line_text[line_text['text'].str.contains('%', regex=True)]['text']))
        if i < header:
            kw['Führendes_VU'] = text
            kw['Führender_%'] = percent
        else:
            kw['Beteiligte_Versicherer'].append(text)
            kw['Beteiligter_%'].append(percent)

    return kw


def policy_selb(df):
    """
    Extract policy selbstbhalt
    """
    kw = {}

    lines = list(set(df['line']))

    for i in range(len(lines)):
        line_df = df[df['line'] == lines[i]]
        perv_line_df = df[df['line'] == lines[i - 1]]

        if len(perv_line_df[perv_line_df['text'].str.contains('Selbstbehalt$', regex=True)]) > 0:
            try:
                kw['SB'] = ' '.join(list(line_df['text']))
                return kw
            except IndexError:
                continue

    return kw


def policy_ander(df):
    """
    Extract Änderungsdatum
    """
    kw = {}

    lines = list(set(df['line']))

    for i in range(len(lines)):
        line_df = df[df['line'] == lines[i]]
        perv_line_df = df[df['line'] == lines[i - 1]]

        if len(perv_line_df[perv_line_df['text'].str.contains('Änderungsdatum', regex=True)]) > 0:
            try:
                kw['gültig ab'] = ' '.join(list(line_df['text']))
                return kw
            except IndexError:
                continue

    return kw


def policy_uternehmen(df):
    """
    Extract Unternehmen
    """
    kw = {}

    block_list = list(set(df['block']))

    for block in range(len(block_list)):
        block_df = df[df['block'] == block_list[block]]

        if len(block_df[block_df['text'].str.contains('Unternehmen')]) > 0 and \
                len(block_df[block_df['text'].str.contains('^\d{5}$')]) > 0:
            kw_name = fill_name(block_df)
            kw['Unternehmen_Name'] = kw_name['VN Name']
            kw['Unternehmen_Strasse'] = kw_name['VN Str']
            kw['Unternehmen_PLZ'] = kw_name['VN PLZ']
            kw['Unternehmen_Ort'] = kw_name['VN Ort']
            return kw

    return kw


def find_values(main_dict, pdf_name):
    """
    Find keyword and values in d & o forms.
    Args:
        main_dict: dictionary, contains dataframes and images of all pages.
        pdf_name: string, name of the document.

    Returns:
        kw: dictionary, contains keyword and values in a single document.
    """

    kw_main = kw_d_and_o()

    df_list = list(main_dict['dfs'].values())
    images = list(main_dict['images'].values())
    pp_images = list(main_dict['pp_images'].values())

    for i, dff in enumerate(df_list):
        df = dff.copy()
        if len(df[df['line'] == 1]) > 20:
            df = find_lines(df)
        image = images[i]
        pp_image = pp_images[i]

        if len(df[df['text'].str.contains('Versicherungsnehmer')]) > 0 and \
                kw_main['VN Name'] == 'NO_VALUE!':
            kw1 = name_and_address(df)

            try:
                val = list(df.index[df['text'].str.contains('Versicherungsmakler')])[0]
                kw1['Makler'] = df['text'][val - 2] + ' ' + df['text'][val - 1]
            except IndexError:
                pass

            kw_main.update(kw1)

        if len(df[df['text'].str.contains('Beginn')]) > 0 and \
                len(df[df['text'].str.contains('Ablauf')]) > 0:
            kw2 = policy_period(df)
            kw_main.update(kw2)

        elif len(df[df['text'].str.contains('Änderungsdatum$')]) > 0:
            kw11 = policy_ander(df)
            kw_main.update(kw11)

        if len(df[df['text'].str.contains('Versicherungsschein-Nr')]) > 0:
            kw3 = policy_number(df)
            kw_main.update(kw3)

        if len(df[df['text'].str.contains('Versicherungssumme')]) > 0:
            kw4 = policy_total(df)
            kw_main.update(kw4)

        if len(df[df['text'].str.contains('Versicherungsprämie')]) > 0:
            kw5 = policy_prame(df)
            kw_main.update(kw5)

        if len(df[df['text'].str.contains('Allgemeinen')]) > 0 and \
                len(df[df['text'].str.contains('Bedingungen')]) > 0:
            kw6 = policy_year(df)
            kw_main.update(kw6)

        if len(df[df['text'].str.contains('Ausfertigungsgrund')]) > 0:
            kw7 = policy_aus(df)
            kw_main.update(kw7)

        if len(df[df['text'].str.contains('Personen')]) > 0 and \
                len(df[df['text'].str.contains('versicherte')]) > 0:
            kw8 = policy_name(df)
            kw_main.update(kw8)

        if len(df[df['text'].str.contains('Risikoträger')]) > 0:
            kw9 = policy_risko(pp_image)
            kw_main.update(kw9)

        if len(df[df['text'].str.contains('Selbstbehalt$')]) > 0:
            kw10 = policy_selb(df)
            kw_main.update(kw10)

        if len(df[df['text'].str.contains('Unternehmen')]) > 0:
            kw11 = policy_uternehmen(df)
            kw_main.update(kw11)

        kw_main['Dateiname'] = pdf_name[:-4]

    return kw_main
