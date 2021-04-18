import re

from utils.constants import kw_architekten, diff_list_architekten
from utils.my_functions import word_similarity


def first_page(df_func):
    """
    Find keywords and values in the first page of the document

    Args:
        df_func: pandas dataframe, contain information of the pdf.

    Returns:
        kw: dictionary, contain keywords and values of the first page.
    """
    # Create an empty dictionary to fill it with variables
    kw = {}

    # Create a copy from dataframe
    df = df_func.copy()

    # Iterate over rows in dataframe to find values
    for index in range(len(df)):

        # update dictionary with the constant key values.
        kw['Dokumentensubtyp'] = 'Haftpflichtversicherung'

        # find word 'versicherung' in dataframe and search for a pattern like "character"+"character" in that line
        if re.sub('[\W_]+', '', df['text'][index].lower()) == 'versicherung' and \
                re.sub('[\W_]+', '', df['text'][index + 1].lower()) == 'ag':
            try:
                kw['Versicherer'] = \
                    re.findall('\D{1}\+\D{1}', ' '.join(list(df[df['line'] == df['line'][index]]['text'])))[0]
            except NameError:
                kw['Versicherer'] = 'NO_VALUE!'
            except IndexError:
                kw['Versicherer'] = 'NO_VALUE!'

        # find word 'agentur' in dataframe and take last two words of the next line
        elif re.sub('[\W_]+', '', df['text'][index].lower()) == 'agentur' and \
                re.sub('[\W_]+', '', df['text'][index - 1].lower()) == 'ihre':
            val = df[df['l-r'] == 1]
            try:
                kw['Makler'] = ' '.join(list(val[val['line'] == df['line'][index] + 1]['text'])[:2])
            except IndexError:
                kw['Makler'] = 'NO_VALUE!'
            except NameError:
                kw['Makler'] = 'NO_VALUE!'

        # find word 'versicherungnr' in dataframe and take the word after it as value
        elif re.sub('[\W_]+', '', df['text'][index].lower()) == 'versicherungnr':
            try:
                val = df[df['left'] > df['left'][index]]
                kw['Policen_ID'] = ' '.join(list(val[val['line'] == df['line'][index]]['text']))
            except NameError:
                kw['Policen_ID'] = 'NO_VALUE!'
            except IndexError:
                kw['Policen_ID'] = 'NO_VALUE!'

        # find word 'versicherungsnehmer' in dataframe and take the words in next three lines after it. for finding plz
        # and ort take the first word of the third line and last word of the last line
        elif re.sub('[\W_]+', '', df['text'][index].lower()) == 'versicherungsnehmer':
            try:
                val = df[df['left'] > df['left'][index] - 500]
                val1 = val[val['left'] < val['left'][index] + val['width'][index] + 400]
                kw['VN Name'] = ' '.join(list(val1[val1['line'] == val1['line'][index] + 1]['text']))
            except IndexError:
                kw['VN Name'] = 'NO_VALUE!'
                kw['VN Str'] = 'NO_VALUE!'
                kw['VN PLZ'] = 'NO_VALUE!'
                kw['VN Ort'] = 'NO_VALUE!'
            else:
                kw['VN Str'] = ' '.join(list(df[df['line'] == df['line'][index] + 2]['text']))
                kw['VN PLZ'] = list(val1[val1['line'] == val1['line'][index] + 3]['text'])[0]
                kw['VN Ort'] = ' '.join(list(val1[(val1['line'] == val1['line'][index] + 3) & (val1['text'].str.contains('\D+', regex=True))]['text']))

        # find word 'gültig' in dataframe and search for a date pattern in that line
        elif re.sub('[\W_]+', '', df['text'][index].lower()) == 'gültig' or \
                re.sub('[\W_]+', '', df['text'][index].lower()) == 'gultig' or \
                re.sub('[\W_]+', '', df['text'][index].lower()) == 'aufgehoben':
            try:
                kw['gültig ab'] = re.findall('\d{2}\.\d{2}\.\d{4}', re.sub('[^\w\.\s]+', '', ' '.join(
                    list(df[df['line'] == df['line'][index]]['text'])).lower()))[0]
            except IndexError:
                kw['gültig ab'] = 'NO_VALUE!'

        # find word 'zahlungsweise' in dataframe and take the next word as value
        elif re.sub('[\W_]+', '', df['text'][index].lower()) == 'zahlungsweise':
            try:
                kw['Zahlweise'] = df['text'][index + 1]
            except IndexError:
                kw['Zahlweise'] = 'NO_VALUE!'

    return kw


def second_page(df_func):
    """
    Find keywords and values in the second page of the document.

    Args:
        df_func: pandas dataframe, contain information of the pdf

    Returns:
        kw: dictionary, contain keywords and values of the first page.
    """

    # Define an empty dictionary to fill it with keys and values.
    kw = {}

    # Create a copy from dataframe.
    df = df_func.copy()

    # Iterate over dataframe rows.
    for index in range(len(df)):

        # find word "jahresnettobeitrag" and search for a price pattern in below and right part of the word
        if re.sub('[\W_]+', '', df['text'][index].lower()) == 'jahresnettobeitrag' and \
                'EUR' in list(df[df['line'] == df['line'][index] + 1]['text']):
            vall = df[df['top'] > df['top'][index]]
            val = vall[vall['left'] > df['left'][index]]
            # values = re.findall('\d{2,3}\,\d{2}', ' '.join(list(val)))
            values = list(val[val['text'].str.contains('\d{2,3}\,\d{2}', regex=True)]['text'])
            try:
                kw['BJP'] = values[1]
            except IndexError:
                kw['JNP'] = 'NO_VALUE!'
                kw['BJP'] = 'NO_VALUE!'
            else:
                kw['JNP'] = values[0]

        # find word "versichertes" and take the word after as value
        elif re.sub('[\W_]+', '', df['text'][index].lower()) == 'versichertes' and \
                re.sub('[\W_]+', '', df['text'][index + 1].lower()) == 'risiko':
            try:
                val = df[(df['left'] > df['left'][index]-10) & (df['l-r'] == 0) & (df['top'] > df['top'][index]-10)].reset_index()
                kw['Risiko'] = val['text'][2]
            except IndexError:
                kw['Risiko'] = 'NO_VALUE!'

        elif re.sub('[\W_]+', '', df['text'][index].lower()) == 'regulierung':
            line_tarikh = list(df[(df['top'] > df['top'][index]) & (df['text'].str.contains('Berechnung'))]['line'])[0]
            try:
                kw['Regulierung bis'] = list(df[(df['line'] == line_tarikh) & (df['text'].str.contains('\d{2}\.\d{2}\.\d{4}', regex=True))]['text'])[0]
            except IndexError:
                kw['Regulierung bis'] = 'NO_VALUE!'

        elif df['text'][index] == 'Aufhebungsgrund':
            try:
                kw['Änderungsgrund'] = ' '.join(list(df[df['line'] == df['line'][index]+1]['text']))
            except IndexError:
                kw['Änderungsgrund'] = 'NO_VALUE!'

    return kw


def third_page(df_func):
    """
    Find keywords and values in the third page of the document.

    Args:
        df_func: pandas dataframe, contain information of the pdf

    Returns:
        kw: dictionary, contain keywords and values of the first page.
    """

    # Define an empty dataframe to update it with keys and values
    kw = {}

    # Create a copy from dataframe.
    df = df_func.copy()

    # Find corresponding keywords
    try:
        vert = list(df[df['text'].str.contains('Vertragsgrundlagen')]['top'])[0]
        vert11 = list(df[df['text'].str.contains('Vertragsgrundlagen')]['left'])[0]
        line1 = list(df[(df['top'] > vert) & (df['text'].str.contains('Ausgabe'))]['line'])
        if len(line1) >= 2:
            kw['AVB'] = list(df[(df['line'] == line1[0]) & (df['left'] > vert11-5)]['text'])[0]
            kw['AVB Stand'] = list(df[(df['line'] == line1[0]) & (df['text'].str.contains('\d{4}', regex=True))]['text'])[-1]
    except IndexError:
        kw['AVB'] = 'NO_VALUE!'
        kw['AVB Stand'] = 'NO_VALUE!'

    try:
        bedi = list(df[df['text'].str.contains('Besondere')]['top'])[-1]
        line2 = list(df[(df['top'] > bedi) & (df['text'].str.contains('Ausgabe'))]['line'])
        if len(line2) >= 1:
            kw['BB'] = list(df[df['line'] == line2[0]]['text'])[0] if len(list(df[df['line'] == line2[0]]['text'])[0]) > 2 else list(df[df['line'] == line2[0]]['text'])[1]
            kw['BB_Stand'] = list(df[(df['line'] == line2[0]) & (df['text'].str.contains('\d{4}', regex=True))]['text'])[-1]
    except IndexError:
        kw['BB'] = 'NO_VALUE!'
        kw['BB_Stand'] = 'NO_VALUE!'

    return kw


def forth_page(df_func):
    """
    Find keywords and values in the forth page of the document.

    Args:
        df_func: pandas dataframe, contain information of the pdf

    Returns:
        kw: dictionary, contain keywords and values of the first page.
    """
    # Define an empty dataframe to update it with keys and values
    kw = {}

    # Create a copy from dataframe.
    df = df_func.copy()

    regex_number = '\d+\.\d{3,4}'

    # Find vertical lines by keywords and find each section
    for index, word in enumerate(df['text']):
        if word == 'Versicherungssummen' and 'DS_PS' not in kw.keys():
            summen = df[df['top'] > df['top'][index]].reset_index()
            linesh1 = list(summen[summen['text'].str.contains('Personenschäden')]['line'])
            linesh2 = list(summen[summen['text'].str.contains('Vermogensschäden')]['line'])
            try:
                a = summen[summen['line'] == linesh1[0]]
                b = list(a[a['text'].str.contains(regex_number, regex=True)]['text'])
                if len(b) == 2:
                    kw['DS_PS'] = b[0]
                    kw['DS_PS_max'] = b[1]
                elif len(b) == 1:
                    kw['DS_PS'] = b[0]
            except IndexError:
                kw['DS_PS'] = 'NO_VALUE!'
                kw['DS_PS_max'] = 'NO_VALUE!'

            try:
                a = summen[summen['line'] == linesh2[0]]
                b = list(a[a['text'].str.contains(regex_number, regex=True)]['text'])
                if len(b) == 2:
                    kw['DS_VS'] = b[0]
                    kw['DS_VS_max'] = b[1]
                elif len(b) == 1:
                    kw['DS_VS'] = b[0]
            except IndexError:
                kw['DS_VS'] = 'NO_VALUE!'
                kw['DS_VS_max'] = 'NO_VALUE!'

        elif word == 'Haftpflicht-Risiken' and df['text'][index - 1] == 'private':
            private = df[df['top'] > df['top'][index]].reset_index()
            linesh1 = list(private[private['text'].str.contains('Vermogensschäden')]['line'])
            linesh2 = list(private[private['text'].str.contains('einzelne')]['line'])
            try:
                a = private[private['line'] == linesh1[0]]
                b = list(a[a['text'].str.contains(regex_number, regex=True)]['text'])
                if len(b) == 2:
                    kw['DS_pauschal_PVS_privat'] = b[0]
                    kw['DS_pauschal_PVS_max_privat'] = b[1]
                elif len(b) == 1:
                    kw['DS_pauschal_PVS_privat'] = b[0]
            except IndexError:
                kw['DS_pauschal_PVS_privat'] = 'NO_VALUE!'
                kw['DS_pauschal_PVS_max_privat'] = 'NO_VALUE!'

            try:
                a = summen[summen['line'] == linesh2[0]]
                b = list(a[a['text'].str.contains(regex_number, regex=True)]['text'])
                if len(b) == 2:
                    kw['DS_pauschal_PVS_privat_jePerson'] = b[0]
                    kw['DS_pauschal_PVS_privat_jePerson_max'] = b[1]
                elif len(b) == 1:
                    kw['DS_pauschal_PVS_privat_jePerson'] = b[0]
            except IndexError:
                kw['DS_pauschal_PVS_privat_jePerson'] = 'NO_VALUE!'
                kw['DS_pauschal_PVS_privat_jePerson_max'] = 'NO_VALUE!'

        elif word == 'Umwelt-/Gewässerschadenhaftpflicht-Risiken':
            gewas = df[df['top'] > df['top'][index]].reset_index()
            linesh1 = list(gewas[gewas['text'].str.contains('Personenschäden')]['line'])
            linesh2 = list(gewas[gewas['text'].str.contains('Sachschäden')]['line'])
            try:
                a = gewas[gewas['line'] == linesh1[0]]
                b = list(a[a['text'].str.contains(regex_number, regex=True)]['text'])
                if len(b) == 2:
                    kw['DS_PS_Umwelt'] = b[0]
                    kw['DS_PS_max_Umwelt'] = b[1]
                elif len(b) == 1:
                    kw['DS_PS_Umwelt'] = b[0]
            except IndexError:
                kw['DS_PS_Umwelt'] = 'NO_VALUE!'
                kw['DS_PS_max_Umwelt'] = 'NO_VALUE!'

            try:
                a = gewas[gewas['line'] == linesh2[0]]
                b = list(a[a['text'].str.contains(regex_number, regex=True)]['text'])
                if len(b) == 2:
                    kw['DS_SS_Umwelt'] = b[0]
                    kw['DS_SS_max_Umwelt'] = b[1]
                elif len(b) == 1:
                    kw['DS_SS_Umwelt'] = b[0]
            except IndexError:
                kw['DS_SS_Umwelt'] = 'NO_VALUE!'
                kw['DS_SS_max_Umwelt'] = 'NO_VALUE!'

        elif word == 'Umweltschaden-Risiken':
            umwelt = df[df['top'] > df['top'][index]].reset_index()
            linesh2 = list(umwelt[umwelt['text'].str.contains('Vermogensschäden')]['line'])
            try:
                a = umwelt[umwelt['line'] == linesh2[0]]
                b = list(a[a['text'].str.contains(regex_number, regex=True)]['text'])
                if len(b) == 2:
                    kw['DS_VS_Umwelt'] = b[0]
                    kw['DS_VS_Umwelt_max'] = b[1]
                elif len(b) == 1:
                    kw['DS_VS_Umwelt'] = b[0]
            except IndexError:
                kw['DS_VS_Umwelt'] = 'NO_VALUE!'
                kw['DS_VS_Umwelt_max'] = 'NO_VALUE!'

    return kw


def fifth_page(df_func):
    """
    Find keywords and values in the fifth page of the document.

    Args:
        df_func: pandas dataframe, contain information of the pdf

    Returns:
        kw: dictionary, contain keywords and values of the first page.
    """
    # Define an empty dataframe to update it with keys and values
    kw = {}

    # Create a copy from dataframe.
    df = df_func[df_func['l-r'] == 0].reset_index().copy()

    try:
        border_bala = list(df[df['text'].str.contains('01\d{6}', regex=True)]['top'])[0]
        border_bala_ = list(df[df['text'].str.contains('01\d{6}', regex=True)]['left'])[0]
        val = df[df['top'] > border_bala]
        border_paein = list(val[(val['text'].str.contains('eigene')) | (val['text'].str.contains('eigens'))]['top'])[0]
        values = val[(val['top'] < border_paein+7) & (val['left'] > border_bala_-10)]
        kw['Wagnis'] = ' '.join(list(values['text']))

    except IndexError:
        kw['Wagnis'] = 'NO_VALUES!'

    try:
        jj = df.index[df['text'].str.contains('Mindestbeitrag')].tolist()[0]
        kw['Mindestbeitrag'] = df['text'][jj + 2]
    except IndexError:
        kw['Mindestbeitrag'] = 'NO_VALUE!'

    try:
        val = list(df[df['text'] == 'Selbstbeteiligung']['top'])[0]
        above_line = list(df[(df['top'] > val) & (df['text'].str.contains('EUR'))]['line'])[0]
        kw['SB'] = list(df[(df['line'] == above_line) & (df['text'].str.contains('\d+[\.\,]\d{3}', regex=True))]['text'])[0]
    except IndexError:
        kw['SB'] = 'NO_VALUE!'

    return kw


def sixth_page(df_func):
    """
    Find keywords and values in the fifth page of the document.

    Args:
        df_func: pandas dataframe, contain information of the pdf

    Returns:
        kw: dictionary, contain keywords and values of the first page.
    """

    def find_value_sixth_page(df_inner, index_inner):
        """
        Find the nearest Selbstbeteiligung in document.

        Args:
            df_inner: pandas dataframe, a dataframe which contain information of the page.
            index_inner: integer, a number for the target value.

        Returns:
            value: string, value for the keyword.
        """
        try:
            dfin = df_inner[df_inner['top'] > df_inner['top'][index_inner] + 5].reset_index()
            if 'level_0' in dfin.columns:
                dfin = dfin.drop(['level_0'], axis=1)

            selb = dfin[dfin['text'].str.contains('selbstbeteiligung', case=False)].reset_index()
            val = dfin[dfin['top'] > selb.iloc[0]['top'] + 3]
            val_ = val[val['line'] < selb.iloc[0]['line'] + 4]
            value = re.findall('\d+\.\d{3,4}', ' '.join(list(val_['text'])))[0]
        except IndexError:
            value = 'NO_VALUE!'

        return value

    # Define an empty dataframe to update it with keys and values
    kw = {}

    # Create a copy from dataframe.
    df = df_func.copy()

    for index, word in enumerate(df['text']):

        if 'Naturschutzpolice' in word:
            police = find_value_sixth_page(df, index)
            kw['SB_Naturschutz'] = police

        elif 'Asbestschäden' in word:
            asbest = find_value_sixth_page(df, index)
            kw['VS_Asbest_SB'] = asbest

        elif 'Umwelthaftpflicht-Basisversicherung' in word:
            basis = find_value_sixth_page(df, index)
            kw['SB_Umwelthaftpflicht'] = basis

        elif 'Diskriminierung' in word:
            diskrim = find_value_sixth_page(df, index)
            kw['SB_Diskriminierung'] = diskrim

        elif 'Privatrisiken' in word:
            kw['PHV_Deckung'] = list(df[(df['line'] == df['line'][index]+1) & (df['l-r'] == 0)]['text'])[-1]

        elif 'Hundehalter' in word and df['text'][index-1] == 'als':
            kw['THV_Deckung'] = df['text'][index-2]

        elif 'Versicherungsfall' in word and df['text'][index-1] == 'je' and 'Vermogensschäden' not in list(df[df['line'] == df['line'][index]-1]['text']):
            try:
                kw['VS_Asbest'] = list(df[(df['line'] == df['line'][index]) & (df['text'].str.contains('\d+\.\d+'))]['text'])[0]
            except IndexError:
                kw['VS_Asbest'] = 'NO_VALUE!'
            try:
                kw['VS_Asbest_max'] = list(df[(df['line'] == df['line'][index]+1) & (df['text'].str.contains('\d+\.\d+'))]['text'])[0]
            except IndexError:
                kw['VS_Asbest_max'] = 'NO_VALUE!'

        elif 'Vermogensschäden' in word and 'pauschal' in ' '.join(list(df[df['line'] == df['line'][index]-1]['text'])):
            try:
                kw['VS_Diskriminierung'] = list(df[(df['line'] == df['line'][index]-1) & (df['text'].str.contains('\d+\.\d+', regex=True))]['text'])[0]
            except IndexError:
                kw['VS_Diskriminierung'] = 'NO_VALUE!'

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

    kw_main = kw_architekten()

    for dff in df_list:

        df = word_similarity(dff, diff_list_architekten)

        if len(df[df['text'].str.contains('Vertragsbeginn')]) >= 1:
            kw1 = first_page(df)
            try:
                kw_main.update(kw1)
            except TypeError:
                pass

        elif (len(df[df['text'].str.contains('Jahresnettobeitrag')]) >= 1 or \
                len(df[df['text'].str.contains('Risiko')]) >= 1 or \
                len(df[df['text'].str.contains('Regulierung')]) >= 1) and \
                len(df[df['text'].str.contains('ausgehändigt')]) < 1:
            kw2 = second_page(df)
            try:
                kw_main.update(kw2)
            except TypeError:
                pass

        elif (len(df[df['text'].str.contains('ausgehändigt')]) >= 1 or \
                len(df[df['text'].str.contains('Ausgabe')]) >= 1) and \
                len(df[df['text'].str.contains('Mindestbeitrag')]) < 1:
            kw3 = third_page(df)
            try:
                kw_main.update(kw3)
            except TypeError:
                pass

        elif len(df[df['text'].str.contains('Versicherungssummen')]) >= 1 and \
                len(df[df['text'].str.contains('Ausgabe')]) < 1 and \
                len(df[df['text'].str.contains('Naturschutzpolice')]) < 1 and \
                len(df[df['text'].str.contains('Mindestbeitrag')]) < 1 and \
                len(df[df['text'].str.contains('Hundehalter')]) < 1:
            kw4 = forth_page(df)
            try:
                kw_main.update(kw4)
            except TypeError:
                pass

        elif (len(df[df['text'].str.contains('Mindestbeitrag')]) >= 1 or
              len(df[df['text'].str.contains('eigene')]) >= 1) and \
                len(df[df['text'].str.contains('Naturschutzpolice')]) < 1 and \
                len(df[df['text'].str.contains('ausgehändigt')]) < 1 and \
                len(df[df['text'].str.contains('Hundehalter')]) < 1:
            kw5 = fifth_page(df)
            try:
                kw_main.update(kw5)
            except TypeError:
                pass

        elif (len(df[df['text'].str.contains('Diskriminierung')]) >= 1 or \
                len(df[df['text'].str.contains('Naturschutzpolice')]) >= 1 or \
                len(df[df['text'].str.contains('Hundehalter')]) >= 1):
            kw6 = sixth_page(df)
            try:
                kw_main.update(kw6)
            except TypeError:
                pass

    kw_main['Dateiname'] = pdf_name[:-4]

    return kw_main
