from utils.constants import kw_elektronik
from utils.ms_lines import find_lines
from utils.utils_elektronik import TabelleGerate
import re
import pandas as pd

def fill_name(block_df):
    """
    Fill keyword dictionary with name and address.

    Args:
        block_df: pandas dataframe, contain block data.

    Returns:
        kw1: dictionary, dictionary filled with name and address.
    """

    kw1 = {}
    block_df = find_lines(block_df)
    plz_df = block_df[block_df['text'].str.contains('^\d{5}$')]
    line_plz_df = list(plz_df['line'])[-1]

    try:
        line_text = ' '.join(list(block_df[block_df['line'] == line_plz_df]['text']))
        line_text = line_text.split()
        kw1['VN PLZ'] = line_text[0]
        kw1['VN Ort'] = ' '.join(line_text[1:])
    except IndexError:
        kw1['VN PLZ'] = 'NO_VALUE!'
        kw1['VN Ort'] = 'NO_VALUE!'

    try:
        kw1['VN Str'] = ' '.join(block_df[block_df['line'] == line_plz_df - 1]['text'])
    except IndexError:
        kw1['VN Str'] = 'NO_VALUE!'

    try:
        if len(set(block_df['line'])) == 4:
            kw1['VN Name'] = ' '.join(block_df[block_df['line'] == line_plz_df - 3]['text'])
            kw1['VN Name'] = kw1['VN Name'] + ' '.join(block_df[block_df['line'] == line_plz_df - 2]['text'])
        elif len(set(block_df['line'])) == 3:
            kw1['VN Name'] = ' '.join(block_df[block_df['line'] == line_plz_df - 2]['text'])
    except IndexError:
        kw1['VN Name'] = 'NO_VALUE!'
    return kw1

def versicherungsorte(df):
    kw = {}
    try:
        y_versicherungsorte = list(df[df['text'].str.contains('Versicherungsort')]['top'])[0]
        x_versicherungsorte = list(df[df['text'].str.contains('Versicherungsort')]['left'])[0]
        y_versicherungssumme = list(df[df['text'].str.contains('Versicherungssumme')]['top'])[0]
        block_df = df[(df['top'] > y_versicherungsorte) & (df['top'] < y_versicherungssumme) & (df['left'] > (x_versicherungsorte - 50)) & (df['text'] != '<LINE>')]
        block_df = find_lines(block_df)
        total_line = max(list(block_df['line']))
        ver_str, ver_plz, ver_ort = [], [], []

        for m in range(total_line):
            line_text = ' '.join(list(block_df[block_df['line'] == (m+1)]['text']))
            tmp = re.findall('\d{5}', line_text)
            if tmp :
                ver_plz.append(tmp[0])
                line_text = line_text.split(ver_plz[-1])
                ver_str.append(line_text[0])
                ver_ort.append(line_text[1])
                kw['Versicherungsort_Str'] = ver_str
                kw['Versicherungsort_PLZ'] = ver_plz
                kw['Versicherungsort_Ort'] = ver_ort
    except:
        pass
    return kw

def name_and_address(df):
    """
    Find values for name and address of policy holder.

    Args:
        df: Pandas DataFrame, dataframe contain page information.

    Returns:
        kw1: dictionary, contain name and address and postal code and city.
    """

    kw1 = {}

    block_list = list(set(df['block']))

    for block in range(len(block_list)):
        block_df = df[df['block'] == block_list[block]]
        perv_block = df[df['block'] == block_list[block - 1]]
        two_prev_blk = df[df['block'] == block_list[block - 2]]

        if len(block_df[block_df['text'].str.contains('^\d{5}$')]) > 0 and \
                (len(block_df[block_df['text'].str.contains('Versicherungsnehmer')]) > 0 or
                 len(perv_block[perv_block['text'].str.contains('Versicherungsnehmer')]) > 0 or
                len(two_prev_blk[two_prev_blk['text'].str.contains('Versicherungsnehmer')]) > 0):

            if len(set(list(block_df['line']))) == 1:
                block_df = find_lines(block_df)
                kw1 = fill_name(block_df)
                return kw1

            else:
                kw1 = fill_name(block_df)
                return kw1

    return kw1


def find_values(main_dict, pdf_name):
    """
    Find keyword and values in elektronik form.
    Args:
        main_dict: dictionary, contains dataframes and images of all pages.
        pdf_name: string, name of the document.

    Returns:
        kw: dictionary, contains keyword and values in a single document.
    """
    flag_GERÄTE = False # flage for Tabelle_GERÄTE
    first_page = True  # First page of Tabelle_GERÄTE
    kw_main = kw_elektronik()
    table = TabelleGerate()
    df_list = list(main_dict['dfs'].values())
    images = list(main_dict['images'].values())
    pp_images = list(main_dict['pp_images'].values())
    kw = {}
    kw['Dateiname'] = pdf_name
    print(pdf_name)
    kw_main.update(kw)
    for i, dff in enumerate(df_list):
        df = dff.copy()
        # ----- VN section
        kw3 = {}
        if len(df[df['text'].str.contains('Versicherungsnehmer')]) and kw_main['Versicherer'] != 'NO_VALUE' and kw_main[
            'VN Str'] == 'NO_VALUE' and kw_main['VN Ort'] == 'NO_VALUE' and kw_main['VN PLZ'] == 'NO_VALUE':
            kw3 = name_and_address(df)
            kw_main.update(kw3)
        # ---- Versicherer section
        line_versicherung = list(df[df['text'].str.match('Versicherung')]['line'])
        kw1 = {}
        if len(line_versicherung) > 0 and kw_main['Versicherer'] == 'NO_VALUE':
            line_text = list(df[df['line'] == line_versicherung[0]]['text'])
            kw1['Versicherer'] = line_text[0]
            kw_main.update(kw1)

        # Policen_ID section
        kw = {}
        if len(df[df['text'].str.contains('(?i)Technische')]) and len(df[df['text'].str.contains('(?i)Versicherungen')]) and kw_main['Policen_ID'] == 'NO_VALUE':
            line_Technische_Versich = list(df[df['text'].str.contains('Technische')]['line'])
            # index_Technische_Versich = df.index(df
            if len(line_Technische_Versich) == 1:
                line_text = ' '.join(df[df['line'] == line_Technische_Versich[0]]['text'])
                if line_text.split('Versicherungen')[1]: kw['Policen_ID'] = line_text.split('Versicherungen')[1]
                kw_main.update(kw)
        elif len(df[df['text'].str.contains('(?i)versicherungsnummer')]) and kw_main['Policen_ID'] == 'NO_VALUE':
            line_versicherungsnummer = df[df['text'].str.contains('Versicherungsnummer')]['line'].to_list()
            if len(line_versicherungsnummer) == 1:
                kw['Policen_ID'] = ' '.join(df[df['line'] == line_versicherungsnummer[0] + 1]['text'])
                kw_main.update(kw)
        # makler section
        kw = {}
        if 'Technische' not in df['text'].tolist() and 'betreut' in df['text'].tolist() and kw_main['Makler'] == 'NO_VALUE':
            block_list = list(set(df['block']))
            for m in range(len(block_list)):
                block_df = df[df['block'] == block_list[m]]
                if 'Versicherungsmakler' in block_df['text'].tolist():
                    block_df = find_lines(block_df)
                    lines = list(set(block_df['line']))
                    try:
                        line_text = ' '.join(block_df[block_df['line'] == lines[1]]['text'])
                        kw['Makler'] = line_text.split('Versicherungsmakler')[0]
                        flag_GERÄTE = True
                        kw_main.update(kw)
                    except:
                        pass
        elif len(df[df['text'].str.contains('(?i)kontak')]) == 1 and kw_main['Makler'] == 'NO_VALUE':
            block_list = list(set(df['block']))
            for m in range(len(block_list)):
                block_df = df[df['block'] == block_list[m]]
                next_blk_df = df[df['block'] == block_list[m]+1]
                if len(block_df[block_df['text'].str.contains('(?i)kontak')]):
                    next_blk_df = find_lines(next_blk_df)
                    # kontak_line = df[df['text'].str.contains('(?i)kontak')]['line'].to_list()
                    # kontak_text = ' '.join(df[df['line'] == (kontak_line[0]+1)])
                    kw['Makler'] = ' '.join(next_blk_df[next_blk_df['line'] == 1]['text'])
                    kw_main.update(kw)
                    break


        # --------- Produkt Section
        if len(df[df['text'].str.contains('(?i)Versicherungsart')]) and kw_main['Produkt'] == 'NO_VALUE':
            kw4 = {}
            line_versichpart = list(df[df['text'].str.contains('Versicherungsart')]['line'])[0]
            kw4['Produkt'] = ' '.join(df[df['line'] == line_versichpart + 1]['text'])
            kw_main.update(kw4)
        elif len(df[df['text'].str.contains('(?i)versichertes')]) and len(df[df['text'].str.contains('(?i)Risiko')]) and kw_main['Produkt'] == 'NO_VALUE':
            kw4 = {}
            line_versichertes = df[df['text'].str.contains('(?i)versichertes')]['line'].to_list()
            line_risiko = df[df['text'].str.contains('(?i)Risiko')]['line'].to_list()
            for m in range(len(line_versichertes)):
                for n in range(len(line_risiko)):
                    if line_versichertes[m] == line_risiko[n]:
                        kw4['Produkt'] = ' '.join(df[df['line'] == line_versichertes[m] + 1]['text'])
                        kw_main.update(kw4)
                        break
        # ---------- gültig ab section
        kw = {}
        if len(df[df['text'].str.contains('Änderung')]) == 1 and kw_main['gültig ab'] == 'NO_VALUE':
            anderung_line = df[df['text'].str.contains('Änderung')]['line'].to_list()
            if len(anderung_line) == 1:
                anderung_text = ' '.join(df[df['line'] == anderung_line[0]]['text'])
                try:
                    tmp = anderung_text.split('Versicherung')[1]
                    tmp = re.findall('\d{2}\.\d{2}\.\d{4}', tmp)
                    if len(tmp) == 1:
                        kw['gültig ab'] = tmp[0]
                        kw_main.update(kw)
                except:
                    pass
        elif len(df[df['text'].str.contains('Beginn')]) == 1 and len(df[df['text'].str.contains('der')]) > 1 and len(df[df['text'].str.contains('Versicherung')]) > 0 and kw_main['gültig ab'] == 'NO_VALUE':
            anderung_line = df[df['text'].str.contains('Beginn')]['line'].to_list()
            if len(anderung_line) == 1:
                anderung_text = ' '.join(df[df['line'] == anderung_line[0]]['text'])
                tmp = anderung_text.split('Versicherung')[1]
                tmp = re.findall('\d{2}\.\d{2}\.\d{4}', tmp)
                if len(tmp) == 1:
                    kw['gültig ab'] = tmp[0]
                    kw_main.update(kw)
        # -------- Versicherungssumme section
        kw = {}
        block_list = list(set(df['block']))
        for block in range(len(block_list)):
            block_df = df[df['block'] == block_list[block]]
            prev_block = df[df['block'] == block_list[block - 1]]

            if len(block_df[block_df['text'].str.contains('\d{2}\.\d{3}')]) > 0 and \
                    len(prev_block[prev_block['text'].str.contains('(?i)Versicherungssumme')]) > 0 and kw_main['Versicherungssumme'] == 'NO_VALUE':
                kw['Versicherungssumme'] = list(block_df[block_df['text'].str.contains('\d{2}\.\d{3}')]['text'])[0]
                kw_main.update(kw)
         # --------- versicherungsorte section
        if len(df[df['text'].str.contains('(?i)versicherungsort')]) and kw_main['gültig ab'] != 'NO_VALUE' and kw_main['Versicherungsort_Str'] == 'NO_VALUE' and kw_main['Versicherungsort_PLZ'] == 'NO_VALUE' and kw_main['Versicherungsort_Ort'] == 'NO_VALUE':
            kw7 = versicherungsorte(df)
            kw_main.update(kw7)
        # --------- JNP section
        kw = {}
        netto_line = df[df['text'].str.contains('(?i)nettojahr')]['line'].to_list()
        if len(netto_line) == 1 and kw_main['JNP'] == 'NO_VALUE':
            netto_line = netto_line[0]
            netto_text = ' '.join(df[df['line'] == netto_line]['text'])
            tmp = re.split('beitrag', netto_text)[1]
            tmp = re.findall('\d+.\d+', tmp)
            if len(tmp) == 1:
                kw['JNP'] = tmp[0]
                kw_main.update(kw)






        # BJP section
        line_BJP = list(df[df['text'].str.contains('jährlich')]['line'])
        kw = {}
        if len(line_BJP) == 1:
            line_text = ' '.join(df[df['line'] == line_BJP[0]]['text'])
            try:
                if line_text.split('Beitrag')[1]: kw['BJP'] = line_text.split('Beitrag')[1]
                kw_main.update(kw)
            except:
                pass

        # AVB section
        kw = {}
        if len(df[df['text'].str.contains('Vertragsgrundlagen')]) > 0:
            line_vertrag = df[df['text'].str.contains('Vertragsgrundlagen')]['line'].to_list()
            if len(line_vertrag) == 1:
                line_vertrag = line_vertrag[0]
                index_Photovo = df.index[df['text'].str.contains('Photovoltaikanlagen|Elektronikversicherung') & (df['line'] > line_vertrag)]
                if len(index_Photovo) == 1:
                    index_mit = np.array(df.index[df['text'].str.contains('mit')].to_list())
                    index_mit = index_mit[index_mit > index_Photovo[0]]
                    if len(index_mit):
                        kw['AVB'] = ' '.join(df.loc[index_Photovo[0]+1:index_mit[0]-1]['text'])
                    kw_main.update(kw)

        # Tabelle_GERÄTE
        Versicherte_exixt, Sache_exist, Selbstbehalt_exist = len(df[df['text'].str.contains("Versicherte")]) > 0, len(df[df['text'].str.contains("Sache")]) > 0,\
                                                             len(df[df['text'].str.contains("Selbstbehalt")]) > 0
        import numpy as np
        if Versicherte_exixt + Sache_exist + Selbstbehalt_exist > 1:
            kw = table.tabelle_gerate(df, first_page=first_page)
            first_page = False
            if kw:
                kw_main.update(kw)
    print(kw_main)
    return kw_main