import pandas as pd
import re

from utils.constants import kw_auvg, diff_list_auvg
from utils.my_functions import word_similarity
from utils.ms_lines import find_lines

pd.options.mode.chained_assignment = None


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
        kw1['VN PLZ'] = list(plz_df['text'])[-1].strip()
    except IndexError:
        kw1['VN PLZ'] = 'NO_VALUE!'

    try:
        line_text = ' '.join(list(block_df[block_df['line'] == list(plz_df['line'])[-1]]['text']))
        kw1['VN Ort'] = line_text.split(list(plz_df['text'])[-1])[-1].strip()
    except IndexError:
        kw1['VN Ort'] = 'NO_VALUE!'

    try:
        kw1['VN Str'] = ' '.join(list(block_df[block_df['line'] == max(list(block_df['line'])) - 1]['text'])).strip()
    except IndexError:
        kw1['VN Str'] = 'NO_VALUE!'

    try:
        name = ' '.join(list(block_df[block_df['line'] < list(plz_df['line'])[-1] - 1]['text']))
        re_list = ['.*:', '.*Firma', '.*Versicherungsnehmer', '.*\.com', '.*Frau', '.*Herrn']
        for item in re_list:
            name = re.sub(item, '', name)
        kw1['VN Name'] = name.strip()
    except IndexError:
        kw1['VN Name'] = 'NO_VALUE!'

    return kw1


def fill_table1(col1, col2, sach_df, miet_df):
    kw = {}

    # array1 = col1[['left', 'top']].to_numpy()
    # array2 = col2[['left', 'top']].to_numpy()
    # dists1 = find_distance(brand_x, brand_y, array1[:, 0],
    #                        array1[:, 1])
    # dists2 = find_distance(brand_x, brand_y, array2[:, 0],
    #                        array2[:, 1])
    # index1 = np.argmax(dists1)
    # index2 = np.argmax(dists2)
    # kw['Summe_Feuer'] = ' '.join(list(col1[col1['line'] == col1['line'][index1]]['text']))
    # kw['SB_Feuer'] = ' '.join(list(col2[col2['line'] == col2['line'][index2]]['text']))

    try:
        brand_top = list(sach_df[sach_df['text'].str.contains('Brand')]['top'])[0]
        leit_top = list(sach_df[sach_df['text'].str.contains('Leitungswasser')]['top'])[0]
        kw['Summe_Feuer'] = ' '.join(
            list(col1[(col1['top'] < leit_top - 10) & (col1['top'] >= brand_top - 10)]['text']))
        kw['SB_Feuer'] = ' '.join(list(col2[(col2['top'] < leit_top - 10) & (col2['top'] >= brand_top - 10)]['text']))
        kw['Summe_Leitungswasser'] = ' '.join(
            list(col1[(col1['top'] > leit_top - 10) & (col1['top'] < leit_top + 10)]['text']))
        kw['SB_Leitungswasser'] = ' '.join(
            list(col2[(col2['top'] > leit_top - 10) & (col2['top'] < leit_top + 10)]['text']))
    except IndexError:
        kw['Summe_Feuer'] = 'NO_VALUE!'
        kw['SB_Feuer'] = 'NO_VALUE!'
        kw['Summe_Leitungswasser'] = 'NO_VALUE!'
        kw['SB_Leitungswasser'] = 'NO_VALUE!'

    try:
        sturm_top = list(sach_df[sach_df['text'].str.contains('Sturm')]['top'])[0]
        kw['Summe_Sturm'] = ' '.join(
            list(col1[(col1['top'] > sturm_top - 10) & (col1['top'] < sturm_top + 10)]['text']))
        kw['SB_Sturm'] = ' '.join(list(col2[(col2['top'] > sturm_top - 10) & (col2['top'] < sturm_top + 10)]['text']))
    except IndexError:
        kw['Summe_Sturm'] = 'NO_VALUE!'
        kw['SB_Sturm'] = 'NO_VALUE!'

    try:
        uber_top = list(sach_df[sach_df['text'].str.contains('Überschwemmung')]['top'])[0]
        glas_top = list(sach_df[sach_df['text'].str.contains('Glasbruch')]['top'])[0]
        kw['Summe_Glas'] = ' '.join(list(col1[(col1['top'] > glas_top - 10) & (col1['top'] < glas_top + 10)]['text']))
        kw['SB_Glas'] = ' '.join(list(col2[(col2['top'] > glas_top - 10) & (col2['top'] < glas_top + 10)]['text']))
        kw['Summe_Überschwemmung'] = ' '.join(list(col1[(col1['top'] < glas_top - 10) &
                                                        (col1['top'] >= uber_top - 10)]['text']))
        kw['SB_Überschwemmung'] = ' '.join(list(col2[(col2['top'] < glas_top - 10) &
                                                     (col2['top'] >= uber_top - 10)]['text']))
    except IndexError:
        kw['Summe_Glas'] = 'NO_VALUE!'
        kw['SB_Glas'] = 'NO_VALUE!'
        kw['Summe_Überschwemmung'] = 'NO_VALUE!'
        kw['SB_Überschwemmung'] = 'NO_VALUE!'

    try:
        uben_top = list(sach_df[sach_df['text'].str.contains('Unbenannte')]['top'])[0]
        kw['Summe_allrisk'] = ' '.join(
            list(col1[(col1['top'] > uben_top - 10) & (col1['top'] < uben_top + 10)]['text']))
        kw['SB_allrisk'] = ' '.join(list(col2[(col2['top'] > uben_top - 10) & (col2['top'] < uben_top + 10)]['text']))
    except IndexError:
        kw['Summe_allrisk'] = 'NO_VALUE!'
        kw['SB_allrisk'] = 'NO_VALUE!'

    try:
        sach_top = list(sach_df[sach_df['text'].str.contains('Sachsubstanzschäden')]['top'])[0]
        kw['Summe_Sonstige'] = ' '.join(
            list(col1[(col1['top'] > sach_top - 10) & (col1['top'] < sach_top + 10)]['text']))
        kw['SB_Sonstige'] = ' '.join(list(col2[(col2['top'] > sach_top - 10) & (col2['top'] < sach_top + 10)]['text']))
    except IndexError:
        kw['Summe_Sonstige'] = 'NO_VALUE!'
        kw['SB_Sonstige'] = 'NO_VALUE!'
    # ______________________________________________________________________________________________________________________
    try:
        brand_top = list(miet_df[miet_df['text'].str.contains('Brand')]['top'])[-1]
        leit_top = list(miet_df[miet_df['text'].str.contains('Leitungswasser')]['top'])[-1]
        kw['Summe_Feuer_MV'] = ' '.join(
            list(col1[(col1['top'] < leit_top - 10) & (col1['top'] >= brand_top - 10)]['text']))
        kw['SB_Feuer_MV'] = ' '.join(
            list(col2[(col2['top'] < leit_top - 10) & (col2['top'] >= brand_top - 10)]['text']))
        kw['Summe_Leitungswasser_MV'] = ' '.join(list(col1[(col1['top'] > leit_top - 10) &
                                                           (col1['top'] < leit_top + 10)]['text']))
        kw['SB_Leitungswasser_MV'] = ' '.join(list(col2[(col2['top'] > leit_top - 10) &
                                                        (col2['top'] < leit_top + 10)]['text']))
    except IndexError:
        kw['Summe_Feuer_MV'] = 'NO_VALUE!'
        kw['SB_Feuer_MV'] = 'NO_VALUE!'
        kw['Summe_Leitungswasser_MV'] = 'NO_VALUE!'
        kw['SB_Leitungswasser_MV'] = 'NO_VALUE!'

    try:
        sturm_top = list(miet_df[miet_df['text'].str.contains('Sturm')]['top'])[-1]
        kw['Summe_Sturm_MV'] = ' '.join(
            list(col1[(col1['top'] > sturm_top - 10) & (col1['top'] < sturm_top + 10)]['text']))
        kw['SB_Sturm_MV'] = ' '.join(
            list(col2[(col2['top'] > sturm_top - 10) & (col2['top'] < sturm_top + 10)]['text']))
    except IndexError:
        kw['Summe_Sturm_MV'] = 'NO_VALUE!'
        kw['SB_Sturm_MV'] = 'NO_VALUE!'

    try:
        uber_top = list(miet_df[miet_df['text'].str.contains('Überschwemmung')]['top'])[-1]
        glas_top = list(miet_df[miet_df['text'].str.contains('Glasbruch')]['top'])[-1]
        kw['Summe_Glas_MV'] = ' '.join(
            list(col1[(col1['top'] > glas_top - 10) & (col1['top'] < glas_top + 10)]['text']))
        kw['SB_Glas_MV'] = ' '.join(list(col2[(col2['top'] > glas_top - 10) & (col2['top'] < glas_top + 10)]['text']))
        kw['Summe_Überschwemmung_MV'] = ' '.join(list(col1[(col1['top'] < glas_top - 10) &
                                                           (col1['top'] >= uber_top - 10)]['text']))
        kw['SB_Überschwemmung_MV'] = ' '.join(list(col2[(col2['top'] < glas_top - 10) &
                                                        (col2['top'] >= uber_top - 10)]['text']))
    except IndexError:
        kw['Summe_Glas_MV'] = 'NO_VALUE!'
        kw['SB_Glas_MV'] = 'NO_VALUE!'
        kw['Summe_Überschwemmung_MV'] = 'NO_VALUE!'
        kw['SB_Überschwemmung_MV'] = 'NO_VALUE!'

    try:
        uben_top = list(miet_df[miet_df['text'].str.contains('Unbenannte')]['top'])[-1]
        kw['Summe_allrisk_MV'] = ' '.join(
            list(col1[(col1['top'] > uben_top - 10) & (col1['top'] < uben_top + 10)]['text']))
        kw['SB_allrisk_MV'] = ' '.join(
            list(col2[(col2['top'] > uben_top - 10) & (col2['top'] < uben_top + 10)]['text']))
    except IndexError:
        kw['Summe_allrisk_MV'] = 'NO_VALUE!'
        kw['SB_allrisk_MV'] = 'NO_VALUE!'

    try:
        sach_top = list(miet_df[miet_df['text'].str.contains('Sonstige')]['top'])[-1]
        kw['Summe_Sonstige_MV'] = ' '.join(
            list(col1[(col1['top'] > sach_top - 10) & (col1['top'] < sach_top + 10)]['text']))
        kw['SB_Sonstige_MV'] = ' '.join(
            list(col2[(col2['top'] > sach_top - 10) & (col2['top'] < sach_top + 10)]['text']))
    except IndexError:
        kw['Summe_Sonstige_MV'] = 'NO_VALUE!'
        kw['SB_Sonstige_MV'] = 'NO_VALUE!'

    return kw


def name_and_address(df):
    """
    Find values for name and address of policy holder.

    Args:
        df: Pandas DataFrame, dataframe contain page information.

    Returns:
        kw1: dictionary, contain name and address and postal code and city.
    """

    kw1 = {'VN Name': 'NO_VALUE!'}

    block_list = list(set(df['block']))

    for block in range(len(block_list)):
        block_df = df[df['block'] == block_list[block]]
        perv_block = df[df['block'] == block_list[block - 1]]

        if ((2 <= len(list(set(block_df['line']))) <= 7 and
             len(block_df[block_df['text'].str.contains('^\d{5}$')]) > 0) or
            len(perv_block[perv_block['text'].str.contains('nehmer')])) and \
                kw1['VN Name'] == 'NO_VALUE!':
            block_df = find_lines(block_df)
            kw1 = fill_name(block_df)

        elif len(block_df[block_df['text'].str.contains('^\d{5}$')]) > 0 and \
                len(list(set(block_df['line']))) == 1:
            line = list(block_df['line'])[0]
            if len(df[(df['line'] == line) & (df['text'].str.contains('Versicherungsort'))]) > 0:
                kw1['structure_Versicherungsort'] = kw_auvg()['structure_Versicherungsort']
                plz = list(block_df[block_df['text'].str.contains('\d{5}')]['text'])[0]
                val = ' '.join(list(block_df['text'])).split(plz)
                st, ort = val[0], val[-1]
                kw1['structure_Versicherungsort']['Versicherungsort_Str'] = st
                kw1['structure_Versicherungsort']['Versicherungsort_PLZ'] = plz
                kw1['structure_Versicherungsort']['Versicherungsort_Ort'] = ort

        elif len(perv_block[perv_block['text'].str.contains('Ausfertigungsgrund')]) > 0:
            kw1['Änderungsgrund'] = ' '.join(list(block_df['text']))

    return kw1


def policy_number(df):
    """
    Extract policy number
    """
    kw = {}

    try:
        line = list(df[df['text'].str.contains('Versicherungsschein')]['line'])[0]
        number = ' '.join(list(df[(df['line'] == line) & (df['text'].str.contains('\d+'))]['text']))
        kw['Policen_ID'] = number
    except IndexError:
        kw['Policen_ID'] = 'NO_VALUE!'

    return kw


def policy_period(df):
    """
    Find values for policy period.

    Args:
        df: Pandas DataFrame, dataframe contain page information.

    Returns:
        kw2: dictionary, contain period of policy.
    """
    kw = {}

    for block in list(set(df['block'])):
        block_df = df[df['block'] == block]

        if len(block_df[block_df['text'].str.contains('\d{2}\.\d{2}\.\d{4}')]) >= 2:
            begin = list(block_df[block_df['text'].str.contains('\d{2}\.\d{2}\.\d{4}')]['text'])[-2]
            end = list(block_df[block_df['text'].str.contains('\d{2}\.\d{2}\.\d{4}')]['text'])[-1]

            kw['Vertragsdauer von'] = begin
            kw['Vertragsdauer bis'] = end
            return kw


def additional_ensurer(df):
    """
    Extract additional ensurers.
    """

    kw = {}

    try:
        line = list(df[df['text'].str.contains('Versicherer')]['line'])[0]
        kw['Versicherer'] = re.sub('.*:', '', ' '.join(list(df[df['line'] == line]['text']))).strip()
    except IndexError:
        kw['Versicherer'] = 'NO_VALUE!'

    return kw


def insurance_broker(df):
    """
    Extract insurance broker
    """
    kw = {}

    try:
        line = list(df[df['text'].str.contains('makler')]['line'])[0]
        kw['Makler'] = re.sub('.*:', '', ' '.join(list(df[df['line'] == line]['text']))).strip()
    except IndexError:
        kw['Makler'] = 'NO_VALUE!'

    return kw


def validation(df):
    """
    Extract validation
    """
    kw = {}

    for block in list(set(df['block'])):
        block_df = df[df['block'] == block]

        if len(block_df[block_df['text'].str.contains('\d{2}\.\d{2}\.\d{4}')]) > 0 and \
                len(block_df[block_df['text'].str.contains('ab:')]) > 0:
            kw['gültig ab'] = list(block_df[block_df['text'].str.contains('\d{2}\.\d{2}\.\d{4}')]['text'])[0]
            return kw

    return kw


def building(df):
    kw = {}
    for block in list(set(df['block'])):
        block_df = df[df['block'] == block]

        if len(block_df[block_df['text'].str.contains('Reines')]) > 0 and \
                len(block_df[block_df['text'].str.contains('Nutzung')]) > 0:
            block_df = find_lines(block_df)
            list_lines = list(set(list(block_df['line'])))
            if 'x' in ' '.join(list(block_df[block_df['line'] == list_lines[0]]['text'])).lower():
                kw['Wohnnutzung'] = True
            else:
                kw['Wohnnutzung'] = False
            if 'x' in ' '.join(list(block_df[block_df['line'] == list_lines[1]]['text'])).lower():
                kw['Gewerbenutzung'] = True
            else:
                kw['Gewerbenutzung'] = False
            if 'x' in ' '.join(list(block_df[block_df['line'] == list_lines[2]]['text'])).lower():
                kw['Mischnutzung'] = True
            else:
                kw['Mischnutzung'] = False

    return kw


def cover(df):
    kw = {}
    for block in list(set(df['block'])):
        block_df = df[df['block'] == block]

        if len(block_df[block_df['text'].str.contains('Haus')]) > 0 and \
                len(block_df[block_df['text'].str.contains('Glasversicherung')]) > 0:
            block_df = find_lines(block_df)
            list_lines = list(set(list(block_df['line'])))
            if 'x' in ' '.join(list(block_df[block_df['line'] == list_lines[0]]['text'])).lower():
                kw['VGV'] = True
            else:
                kw['VGV'] = False
            if 'x' in ' '.join(list(block_df[block_df['line'] == list_lines[1]]['text'])).lower():
                kw['Glas'] = True
            else:
                kw['Glas'] = False
            if 'x' in ' '.join(list(block_df[block_df['line'] == list_lines[2]]['text'])).lower():
                kw['HUG'] = True
            else:
                kw['HUG'] = False

    return kw


def table(df_main):
    dff = df_main.copy()

    df = word_similarity(dff, diff_list_auvg[0])

    try:
        hoc = df[df['text'].str.contains('Höchstentschädigung')].reset_index()
        selb = df[df['text'].str.contains('Selbstbeteiligung')].reset_index()

        x1, y1, w1, h1 = hoc['left'][1], hoc['top'][1], hoc['width'][1], hoc['height'][1]
        x2, y2, w2, h2 = selb['left'][1], selb['top'][1], selb['width'][1], selb['height'][1]

        col1_border = [x1 - (w1 / 2), x1 + (w1 / 2)]
        col2_border = [x2 - (w2 / 2), x2 + (w2 / 2)]

        col1 = df[(df['top'] > y1) &
                  (df['left'] > col1_border[0]) &
                  (df['left'] < col1_border[1]) &
                  (df['text'].str.contains('[A-Za-z0-9]{2,}'))].reset_index()
        col2 = df[(df['top'] > y2) &
                  (df['left'] > col2_border[0]) &
                  (df['left'] < col2_border[1]) &
                  (df['text'].str.contains('[A-Za-z0-9]{2,}'))].reset_index()

        col1 = find_lines(col1)
    except IndexError:
        return {}

    try:
        sach_top = list(df[df['text'].str.contains('Sachsubstanzschäden')]['top'])[0]
        sach_down = list(df[df['text'].str.contains('Mietverlust')]['top'])[0]
        miet_down = list(df[df['text'].str.contains('Grundbesitzer-Haftpflicht')]['top'])[0]
        sach_df = df[(df['top'] > sach_top) & (df['top'] < sach_down)].reset_index()
        miet_df = df[(df['top'] > sach_down) & (df['top'] < miet_down - 5)].reset_index()
    except IndexError:
        sach_df = df
        miet_df = df

    kw = fill_table1(col1, col2, sach_df, miet_df)

    try:
        haus_line = list(df[df['text'].str.contains('Grundbesitzer-Haftpflicht')]['line'])[0]
        haus = ' '.join(list(df[df['line'] == haus_line]['text'])).split('Grundbesitzer-Haftpflicht')[-1]
        kw['Summe_HUG'] = haus.strip()
    except IndexError:
        kw['Summe_HUG'] = 'NO_VALUE!'

    return kw


def annual_fee(df_main):
    dff = df_main.copy()
    kw = {}

    df = word_similarity(dff, diff_list_auvg[1])

    block_list = list(set(df['block']))

    for block in range(len(block_list)):
        block_df = df[df['block'] == block_list[block]]
        perv_block = df[df['block'] == block_list[block - 1]]

        if len(block_df[block_df['text'].str.contains('\d{1,3}\,\d{1,3}')]) == 2:
            if 'JNP' not in list(kw.keys()):
                kw['JNP'] = re.sub('[^0-9,.]', '',
                                   list(block_df[block_df['text'].str.contains('\d{1,3}\,\d{1,3}')]['text'])[0])
                kw['BJP'] = re.sub('[^0-9,.]', '',
                                   list(block_df[block_df['text'].str.contains('\d{1,3}\,\d{1,3}')]['text'])[1])
            else:
                if len(block_df[block_df['text'].str.contains('Erstbeitrag')]) > 0 or \
                        len(perv_block[perv_block['text'].str.contains('Erstbeitrag')]) > 0 or \
                        len(perv_block[perv_block['text'].str.contains('Erhebung')]) > 0:
                    continue
                else:
                    kw['HUG_JNP'] = re.sub('[^0-9,.]', '',
                                           list(block_df[block_df['text'].str.contains('\d{1,3}\,\d{1,3}')]['text'])[0])
                    kw['HUG_BJP'] = re.sub('[^0-9,.]', '',
                                           list(block_df[block_df['text'].str.contains('\d{1,3}\,\d{1,3}')]['text'])[1])

        elif len(perv_block[perv_block['text'].str.contains('Jahresbeitrag')]) > 0 and \
                len(perv_block[perv_block['text'].str.contains('Gebäude')]) > 0 and \
                len(perv_block[perv_block['text'].str.contains('\d+')]) == 0:
            if 'JNP' not in list(kw.keys()):
                try:
                    kw['JNP'] = re.sub('[^0-9,.]', '',
                                       list(block_df[block_df['text'].str.contains('\d{1,3}\,\d{1,3}')]['text'])[0])
                    kw['BJP'] = re.sub('[^0-9,.]', '',
                                       list(block_df[block_df['text'].str.contains('\d{1,3}\.\d{1,3}\.')]['text'])[0])
                except IndexError:
                    continue

        elif len(block_df[block_df['text'].str.contains('Bedingungen')]) > 0 and \
                len(block_df[(block_df['text'].str.contains('gelten'))]) > 0:
            if 'AVB' not in list(kw.keys()):
                try:
                    val = list(block_df[block_df['text'].str.contains('\(.+\)', regex=True)]['text'])[0]
                    kw['AVB'] = re.sub('[^A-Za-z-0-9_]', '', val)
                except IndexError:
                    continue

    return kw


def find_values(df_list, pdf_name):
    """
    Find keyword and values in Architekten forms.
    Args:
        df_list: list, contains dataframe of all pages.
        pdf_name: string, name of the document.

    Returns:
        kw: dictionary, contains keyword and values in a single document.
    """

    kw_main = kw_auvg()

    for i, dff in enumerate(df_list):
        df = dff.copy()

        if (kw_main['VN PLZ'] == 'NO_VALUE!' or kw_main['VN PLZ'] == '') and \
                (len(df[df['text'].str.contains('Versicherungsnehmerin')]) > 0 or
                 len(df[df['text'].str.contains('Versicherungsnehmer')]) > 0):
            kw1 = name_and_address(df)
            kw_main.update(kw1)

        if (kw_main['Policen_ID'] == 'NO_VALUE!' or kw_main['Policen_ID'] == '') and \
                len(df[df['text'].str.contains('Versicherungsschein')]) > 0:
            kw2 = policy_number(df)
            kw_main.update(kw2)

        if (kw_main['Vertragsdauer von'] == 'NO_VALUE!' or
            kw_main['Vertragsdauer von'] == '') and \
                len(df[df['text'].str.contains('Vertragsdauer')]) > 0:
            kw3 = policy_period(df)
            kw_main.update(kw3)

        if (kw_main['Versicherer'] == 'NO_VALUE!' or
            kw_main['Versicherer'] == '') and \
                len(df[df['text'].str.contains('Versicherer')]) > 0:
            kw4 = additional_ensurer(df)
            kw_main.update(kw4)

        if (kw_main['Makler'] == 'NO_VALUE!' or
            kw_main['Makler'] == '') and \
                len(df[df['text'].str.contains('makler')]) > 0:
            kw5 = insurance_broker(df)
            kw_main.update(kw5)

        if (kw_main['gültig ab'] == 'NO_VALUE!' or
            kw_main['gültig ab'] == '') and \
                (len(df[df['text'].str.contains('Gültig')]) > 0 or
                 len(df[df['text'].str.contains('Gultig')]) > 0):
            kw6 = validation(df)
            kw_main.update(kw6)

        if kw_main['Wohnnutzung'] == 'NO_VALUE!' and \
                len(df[df['text'].str.contains('Reines')]) > 0:
            kw7 = building(df)
            kw_main.update(kw7)

        if kw_main['VGV'] == 'NO_VALUE!' and \
                len(df[df['text'].str.contains('Glasversicherung')]) > 0:
            kw8 = cover(df)
            kw_main.update(kw8)

        if len(df[df['text'].str.contains('Höchstentschädigungen')]) > 0:
            kw9 = table(df)
            kw_main.update(kw9)

        if len(df[df['text'].str.contains('Jahresbeitrag')]) > 0:
            kw10 = annual_fee(df)
            kw_main.update(kw10)

        kw_main['Dateiname'] = pdf_name[:-4]

    return kw_main
