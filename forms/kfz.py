import pandas as pd
import re

from utils.constants import kw_kfz, diff_list_kfz
from utils.my_functions import word_similarity
from utils.ms_lines import find_lines


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
        re_list = ['.*:', '.*Firma', '.*Versicherungsnehmer', '.*\.com']
        for item in re_list:
            name = re.sub(item, '', name)
        kw1['VN Name'] = name
    except IndexError:
        kw1['VN Name'] = 'NO_VALUE!'

    return kw1


def policy_company(df):
    """
    Find values for policy company.

    Args:
        df: Pandas DataFrame, dataframe contain page information.

    Returns:
        kw0: dictionary, contain name of policy company.
    """
    kw0 = {}

    for block in list(set(df['block'])):
        block_df = df[df['block'] == block]

        if 1 <= len(list(set(block_df['line']))) <= 3 and \
                len(block_df[block_df['u-d'] == 1]) == 0 and \
                (len(block_df[block_df['text'] == 'Versicherung']) > 0 or
                 len(block_df[block_df['text'].str.contains('Versicherungs-AG')]) > 0):

            try:
                verse_line = list(block_df[block_df['text'].str.contains('Versicherung')]['line'])[0]
                kw0['Versicherer'] = re.sub('Versicherung.*', '', ' '.join(list(
                    block_df[block_df['line'] == verse_line]['text']))).strip()
                if kw0['Versicherer'] == '':
                    kw0['Versicherer'] = re.sub('Versicherung.*', '', ' '.join(list(
                        block_df['text']))).strip()
            except IndexError:
                kw0['Versicherer'] = 'NO_VALUE!'

            break

    if kw0 == {}:
        try:
            line_verse = list(df[df['text'].str.match('Versicherer')]['line'])[0]
            kw0['Versicherer'] = re.sub('Versicherung.*', '', ' '.join(
                list(df[df['line'] == line_verse + 1]['text']))).strip()
        except IndexError:
            kw0['Versicherer'] = 'NO_VALUE!'

    return kw0


def name_and_address(df):
    """
    Find values for name and address of policy holder.

    Args:
        df: Pandas DataFrame, dataframe contain page information.

    Returns:
        kw1: dictionary, contain name and address and postal code and city.
    """

    kw1 = {}

    for block in list(set(df['block'])):
        block_df = df[df['block'] == block]

        down_down_part = list(df[df['text'] == '<END>']['top'])[0] - (
                (list(df[df['text'] == '<END>']['top'])[0] / 2) / 2)

        if (3 <= len(list(set(block_df['line']))) <= 7 and
            len(block_df[block_df['l-r'] == 0]) > 0 and
            len(block_df[block_df['text'].str.contains('^\d{5}$')]) > 0 and
            list(block_df[block_df['text'].str.contains('^\d{5}$')]['top'])[0] < down_down_part) or \
                (len(block_df[block_df['text'].str.contains('Firma')]) > 0 and
                 len(block_df[block_df['text'].str.contains('^\d{5}$')]) > 0):

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

    Args:
        df: Pandas DataFrame, dataframe contain page information.

    Returns:
        kw2: dictionary, contain period of policy.
    """
    kw2 = {}

    for block in list(set(df['block'])):
        block_df = df[df['block'] == block]

        if len(block_df[block_df['text'].str.contains('\d{2}\.\d{2}\.\d{4}')]) >= 2 or \
                (len(block_df[block_df['text'].str.contains('\d{2}\.\d{2}\.\d{4}')]) == 1 and
                 len(block_df[block_df['text'].str.contains('bis')]) == 1):
            if len(block_df[block_df['text'].str.contains('\d{2}\.\d{2}\.\d{4}')]) >= 2:
                begin = list(block_df[block_df['text'].str.contains('\d{2}\.\d{2}\.\d{4}')]['text'])[-2]
                end = list(block_df[block_df['text'].str.contains('\d{2}\.\d{2}\.\d{4}')]['text'])[-1]

                kw2['gültig ab'] = begin
                kw2['Ablaufdatum'] = end
                return kw2

            elif len(block_df[block_df['text'].str.contains('\d{2}\.\d{2}\.\d{4}')]) > 0 and \
                    len(block_df[block_df['text'].str.match('bis')]) > 0:
                kw2['Ablaufdatum'] = list(block_df[block_df['text'].str.contains('\d{2}\.\d{2}\.\d{4}')]['text'])[-1]
                return kw2

    try:
        val = df[df['text'].str.match('Beginn')]
        begin = df[(df['top'] > list(val['top'])[0]) & (df['text'].str.contains('\d{2}\.\d{2}\.\d{4}'))]
        kw2['gültig ab'] = list(begin['text'])[0]
    except IndexError:
        kw2['gültig ab'] = 'NO_VALUE!'

    try:
        val = df[df['text'].str.match('Ablauf')]
        end = df[(df['top'] > list(val['top'])[0]) & (df['text'].str.contains('\d{2}\.\d{2}\.\d{4}'))]
        kw2['Ablaufdatum'] = list(end['text'])[0]
    except IndexError:
        kw2['Ablaufdatum'] = 'NO_VALUE!'

    return kw2


def policy_number(df):
    """
    Find values for policy number.

    Args:
        df: Pandas DataFrame, dataframe contain page information.

    Returns:
        kw3: dictionary, contain number of policy.
    """
    kw3 = {}

    for block in list(set(df['block'])):
        block_df = df[df['block'] == block].reset_index()

        if len(block_df[block_df['text'].str.contains('Versicherungsscheinnummer')]) > 0 or \
                len(block_df[block_df['text'].str.contains('Versicherungsnummer')]) > 0 or \
                len(block_df[block_df['text'].str.match('Nr.')]) > 0:

            if len(block_df[block_df['text'].str.contains('\d+')]):
                keyword = block_df[(block_df['text'].str.contains('Versicherungsscheinnummer')) |
                                   (block_df['text'].str.contains('Versicherungsnummer')) |
                                   (block_df['text'].str.match('Nr.'))]
                if len(keyword) > 0:
                    index = block_df.index[(block_df['text'].str.contains('Versicherungsscheinnummer')) |
                                           (block_df['text'].str.contains('Versicherungsnummer')) |
                                           (block_df['text'].str.match('Nr.'))]
                    try:
                        kw3['Policen_ID'] = re.sub('eine.*', '', ' '.join(list(
                            block_df.iloc[index[0] + 1:]['text']))).strip()
                    except IndexError:
                        kw3['Policen_ID'] = 'NO_VALUE!'

                    return kw3

            else:
                for i in range(block, block + 3):
                    a = df[df['block'] == i]

                    if len(set(list(a['line']))) == 1 and \
                            len(a[a['text'].str.contains('\d+')]):
                        kw3['Policen_ID'] = ' '.join(list(a['text']))
                        return kw3

    return kw3


def additional_insurers(df):
    """
    Find values for additional insurers.

    Args:
        df: Pandas DataFrame, dataframe contain page information.

    Returns:
        kw4: dictionary, contain additional insurer.
    """
    kw4 = {}

    for block in list(set(df['block'])):
        block_df = df[df['block'] == block].reset_index()

        if len(block_df[((block_df['text'].str.contains('Weitere')) |
                         (block_df['text'].str.contains('Mitversicherte')))]) > 0 and \
                len(block_df[(block_df['text'].str.contains('Versicherungsnehmer')) |
                             (block_df['text'].str.contains('mitversicherte')) |
                             (block_df['text'].str.contains('Mitversicherte')) |
                             (block_df['text'].str.contains('Versicherungs')) |
                             (block_df['text'].str.contains('Unternehmen'))]) > 0 and \
                len(block_df[block_df['text'].str.contains('Versichert')]) < 1:

            kw4[f'weitere_Unternehmen'] = {}

            c = df[df['block'] == block + 1]

            if len(df[(df['block'] == block) & (df['text'].str.contains('GmbH'))]):
                j = 0
            elif len(c[(c['text'].str.contains('Insured')) |
                       (c['text'].str.contains('insured'))]) > 0:
                j = 2
            else:
                j = 1

            for i in range(1, len(set(list(df[df['block'] == block + j]['line']))) + 1):
                a = df[df['block'] == block + j]
                line_list = list(set(a['line']))
                b = ' '.join(list(a[a['line'] == line_list[i - 1]]['text']))
                if 'Versicherungsnehmer' in b:
                    continue

                if len(b) <= 3 and i != 1:
                    lenn = len(list(kw4['weitere_Unternehmen']))
                    kw4['weitere_Unternehmen'][f'{lenn}'] = kw4[f'weitere_Unternehmen'][f'{lenn}'] + ' ' + b

                else:
                    lenn = len(list(kw4['weitere_Unternehmen']))
                    kw4['weitere_Unternehmen'][f'{lenn + 1}'] = b

            return kw4

        #                 if len(b) <= 3 and i != 1:
        #                     lenn = len(list(kw4['weitere_Unternehmen']))
        #                  kw4['weitere_Unternehmen'][f"{lenn + 1}"] = kw4[f'weitere_Unternehmen'][f'{lenn}'] + ' ' + b
        #
        #                 else:
        #                     lenn = len(list(kw4['weitere_Unternehmen']))
        #                     kw4['weitere_Unternehmen'][f'{lenn + 1}'] = b

    return kw4


def indemnity(dff):
    """
    Find values for indemnity.

    Args:
        dff: Pandas DataFrame, dataframe contain page information.

    Returns:
        kw5: dictionary, contain indemnity.
    """

    # copy = dff.copy()
    #
    # df = word_similarity(copy, diff_list_kfz)
    #
    # try:
    #     top = \
    #         dff.index[
    #                  (dff['text'].str.contains('Deckungssummen')) | (dff['text'].str.contains('Höchstersatzleistung')) |
    #                  (dff['text'].str.contains('Versicherungssumme'))][0]
    # except IndexError:
    #     pass
    #
    # return df, fire
    #
    # excel = pd.read_excel('/home/deep/Workspace/Data/ocr/Versicherungsbestätigungen/json_versicherungsbestätigung.xlsx')
    #
    # excel = excel.drop(['Json_Name', 'colour', 'JSON Attribut'], axis=1)
    # excel = excel.drop([23])
    #
    # excel = excel[19:].reset_index().drop(['index'], axis=1)
    #
    # for row in range(len(excel)):
    #     for item in list(excel.iloc[row].dropna()):
    #         listam = item.split('+')
    #
    #         for word in listam:

    index = dff.index[(dff['text'].str.contains('Deckungssummen')) |
                      (dff['text'].str.contains('Höchstersatzleistung')) |
                      (dff['text'].str.contains('Versicherungssumme'))][0]

    dff = dff[index:]

    prices = dff[(dff['text'].str.contains('\d{1,3}\,\d{3}\,\d{3}', regex=True)) |
                 (dff['text'].str.contains('\d{1,3}\.\d{3}\.\d{3}', regex=True))]

    if list(prices[prices['l-r'] == 0]['text']) == list(prices[prices['l-r'] == 1]['text']):
        df = dff[dff['l-r'] == 0].reset_index()
    else:
        df = dff.copy()

    if len(prices):
        for i in set(list(prices['line'])):
            line = dff[dff['line'] == i]

    return prices


def append_dataframe(df_c, df):
    """
    Append a dataframe to main dataframe.

    Args:
        df_c: pandas dataframe, main dataframe.
        df: pandas dataframe, append this to the main dataframe.

    Returns:
        df_c: pandas dataframe, dataframe with appended information.
    """
    if not len(df_c):
        df_c = df_c.append(df, ignore_index=True)

    else:
        df['top'][:-1] += list(df_c[df_c['text'].str.contains('<END>')]['top'])[0]
        df['line'][:-1] += max(list(df_c['line']))
        df['block'][:-1] += max(list(df_c['block']))

        df_c = df_c.append(df, ignore_index=True)

    return df_c


def find_values(df_list, pdf_name):
    """
    Find keyword and values in kfz forms.
    Args:
        df_list: list, contains dataframe of all pages.
        pdf_name: string, name of the document.

    Returns:
        kw: dictionary, contains keyword and values in a single document.
    """

    kw_main = kw_kfz()
    df_concat = pd.DataFrame(columns=['text', 'left', 'top', 'width', 'height', 'line', 'block', 'l-r', 'u-d', 'conf'])

    for i, dff in enumerate(df_list):
        df = dff.copy()

        if (kw_main['Versicherer'] == 'NO_VALUE!' or kw_main['Versicherer'] == '') and \
                (len(df[df['text'].str.contains('Versicherung')]) > 0 or
                 len(df[df['text'].str.contains('Versicherer')]) > 0):
            kw0 = policy_company(df)
            kw_main.update(kw0)

        if (kw_main['VN PLZ'] == 'NO_VALUE!' or kw_main['VN PLZ'] == '') and \
                (len(df[df['text'].str.contains('Versicherungsnehmerin')]) > 0 or
                 len(df[df['text'].str.contains('Versicherungsnehmer')]) > 0):
            kw1 = name_and_address(df)
            kw_main.update(kw1)

        if kw_main['gültig ab'] == 'NO_VALUE!' or kw_main['gültig ab'] == '':
            kw2 = policy_period(df)
            kw_main.update(kw2)

        if kw_main['Policen_ID'] == 'NO_VALUE!' or kw_main['Policen_ID'] == '':
            kw3 = policy_number(df)
            kw_main.update(kw3)

        if kw_main['weitere_Unternehmen'] == 'NO_VALUE!' or kw_main['weitere_Unternehmen'] == '':
            kw4 = additional_insurers(df)
            kw_main.update(kw4)

        df_concat = append_dataframe(df_concat, df)

    kw5 = indemnity(df_concat)

    kw_main['Dateiname'] = pdf_name[:-4]

    return kw_main
