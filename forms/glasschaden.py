# Import libraries
from utils.utils import remove_lines, json_accuracy
from utils.my_functions import below_word
from utils.constants import synonyms
import pandas as pd
import cv2
import re


def processing_image(img):
    """
    Perform preprocessing tasks on image to remove noises with openCV.

    Arguments:
    img -- string, path of an image which want to perform preprocessing on it.

    Return:
    image -- numpy array, array of output image which performed preprocessing tasks on it.
    """
    image = cv2.imread(img, cv2.IMREAD_GRAYSCALE)  # Convert RGB image to grayscale

    image = remove_lines(image, horizontal=True, vertical=True, thick=2)

    # Setting all background pixels to 0 and foreground pixels to 255
    image = cv2.threshold(image, 150, 255, cv2.THRESH_BINARY)[1]

    return image


def invoice_name(df_func):
    """
    Custom structures for name and address in the invoices

    Arguments:
    df -- pandas dataframe, a dataframe which contain information of the invoice

    Return:
    name_list -- list, contain values of names and addresses in invoices
    """

    name_list = []
    workshop_list = []
    vn_regex = '(\s\d{5}\s[^\W0-9]{3,10}|\-\d{5}\s\D+)'

    new_df = df_func.copy()

    new_df['text'] = new_df['text'].apply(lambda x: x.lower())  # convert to lowercase all words

    up = new_df[new_df['u-d'] == 0]
    up_left = up[up['l-r'] == 0].reset_index()  # split upper left corner of the image

    for line in list(set(up_left['line'])):
        workshop_data = re.search(vn_regex, ' '.join(list(up_left[up_left['line'] == line]['text'])))

        if workshop_data and workshop_data.start() != 0:
            workshop_list = ' '.join(list(up_left[up_left['line'] == line]['text']))
            break

    # Find all group of texts which matches the given pattern
    match_texts = re.findall(vn_regex, ' '.join(list(up_left['text'])).lower())

    # if the founded pattern is more than 3 the target value is second one , else it is last one
    if len(match_texts) > 2:
        target_value = match_texts[1].strip().strip('-')
    elif len(match_texts) <= 2 and match_texts:
        target_value = match_texts[-1].strip().strip('-')
    else:
        target_value = []

    if target_value:
        # Iterate over words to find target value
        for index in range(1, len(up_left)):

            if target_value in up_left['text'][index - 1] + ' ' + up_left['text'][index] and up_left['text'][
                index - 1] == \
                    list(up_left[up_left['line'] == up_left['line'][index]]['text'])[0]:  # find target value

                cutter = up_left[up_left['left'] < up_left['left'][index] + 300]  # remove right part of the corner
                lines = sorted(list(set(cutter['line'])))

                index_line = lines.index(cutter['line'][index])

                if len(list(up_left[up_left['line'] == up_left['line'][index] - 3]['text'])) <= 6 and 'firma' not in \
                        list(up_left[up_left['line'] == up_left['line'][index] - 3]['text']) and 'fa.' not in list(
                    up_left[up_left['line'] == up_left['line'][index] - 3]['text']):
                    name_list.append(' '.join(list(cutter[cutter['line'] == lines[index_line - 3]]['text'])))
                name_list.append(' '.join(list(cutter[cutter['line'] == lines[index_line - 2]]['text'])))
                name_list.append(' '.join(list(cutter[cutter['line'] == lines[index_line - 1]]['text'])))
                name_list.append(' '.join(list(cutter[cutter['line'] == lines[index_line]]['text'])))

                break

    # if the above method didn't work program search for word 'frima' and base on this word extract values
    if not name_list:
        for index in range(len(new_df)):
            if new_df['text'][index].lower() == 'firma' and new_df['l-r'][index] == 0 and new_df['u-d'][index] == 0:
                val = new_df[new_df['top'] > new_df['top'][index] + 5]
                val0 = val[val['left'] > new_df['left'][index] - 10]
                val1 = val0[val0['top'] < new_df['top'][index] + 200]
                val2 = val1[val1['left'] < new_df['left'][index] + 375]
                val_list = [' '.join(list(val2[val2['line'] == line]['text'])) for line in
                            sorted(set(list(val2['line'])))]
                name_list.append(val_list)  # if firma keyword founded, then create a template with fixed sizes
                break

    return name_list, workshop_list


def invoice_date(df_func, syns_df):
    """
    Custom structures for invoice date in the invoices

    Arguments:
    df -- pandas dataframe, a dataframe which contain information of the invoice
    syns_df -- pandas dataframe, a dataframe contain synonyms of words

    Return:
    date -- list, values of date in invoices
    """

    # define variables
    new_df = df_func.copy()
    date_regex = '(\d{2}\S\d{2}\.\d{2,4})'
    date_list = []
    date = 'NO VALUE!'

    # split the upper side of the page
    up = new_df[new_df['u-d'] == 0].reset_index()

    # iterate over the upper side to find words in synonym dictionary
    for i in range(len(up)):

        if re.sub('[\W_]+', '', up['text'][i].lower()) in list(syns_df['invoice date'].dropna()):
            if re.sub('[\W_]+', '', up['text'][i].lower()) == 'weiden' and re.sub('[\W_]+', '',
                                                                                  up['text'][i + 1].lower()) != 'den':
                continue

            line_text = up[i:]
            # find all words which match the date pattern
            date_list = re.findall(date_regex,
                                   ' '.join(list(line_text[line_text['line'] == line_text['line'][i]]['text'])))

            if date_list:
                break
            else:
                date_list = below_word(up, i, date_regex)
                if date_list:
                    break
                else:
                    date_list = below_word(up, i, date_regex, column_or_line='line')
                    if date_list:
                        break

    # update the date variable
    if type(date_list) == list and date_list:
        date = date_list[0]
    elif type(date_list) == str:
        date = date_list

    return date


def invoice_number(df_func, syns_df):
    """
    Custom structures for invoice number in the invoices

    Arguments:
    df -- pandas dataframe, a dataframe which contain information of the invoice
    syns_df -- pandas dataframe, a dataframe contain synonyms of words

    Return:
    number -- list, values for number of invoices
    """

    # define variables
    new_df = df_func.copy()
    number_regex = '(\d{5,6}\-\d{5,6}|\d{5,9}|\w{2}\d{5,9})'
    remove_regex = '[^A-Za-z0-9\s\-\.]+'
    number = []

    # split the upper side of the page
    up = new_df[new_df['u-d'] == 0].reset_index()

    up['text'] = up['text'].apply(lambda x: re.sub(remove_regex, '', x.lower()))

    # iterate over the upper side to find words in synonym dictionary
    for i in range(1, len(up)):

        number_regex = '(\d{5,6}\-\d{5,6}|\d{5,9}|\w{2}\d{5,9})'

        for syn in list(syns_df['invoice number'].dropna()):
            if syn.lower() in up['text'][i] or syn.lower() in up['text'][i - 1] + up['text'][i] and not number:

                if syn == 'rechnungsnummer':
                    number_regex = '(\d{5,9})'

                line_text = up[i:]
                # find all words which match the date pattern
                number_list = re.findall(number_regex,
                                         ' '.join(list(line_text[line_text['line'] == line_text['line'][i]]['text'])))

                if number_list:
                    number = number_list[0]
                else:
                    number_list = below_word(up, i, number_regex)
                    if number_list:
                        number = number_list

    if number:
        pass
    else:
        for i in range(len(up)):
            if up['text'][i] == 'rechnung':
                line_text = up[i:]
                # find all words which match the date pattern
                number_list = re.findall(number_regex,
                                         ' '.join(list(line_text[line_text['line'] == line_text['line'][i]]['text'])))

                if number_list:
                    number = number_list[0]
                else:
                    number_list = below_word(up, i, number_regex)
                    if number_list:
                        number = number_list

    return number


def invoice_plate(df_func, plate_list):
    """
    Custom structures for plate number in the invoices

    Arguments:
    df -- pandas dataframe, a dataframe which contain information of the invoice
    plate_list -- list, values for plate number of vehicles in invoices

    Return:
    plate_list -- list, values for plate number of vehicles in invoices
    """

    # define the regex patterns
    new_df = df_func.copy()
    plate_regex = '([A-Z]{2,3}\-[A-Z]{1,2}\s\d{2,4}' \
                  '|[A-Z]{2,3}\-[A-Z]{1,2}\-\d{2,4}' \
                  '|[A-Z]{2,3}\-[A-Z]{1,2}\d{2,4})'
    plate2_regex = '[A-Z]{2,3}\s[A-Z]{1,2}\s\d{2,4}'

    # split the upper side of the page
    up = new_df[new_df['u-d'] == 0]

    listam = re.findall(plate_regex, ' '.join(list(up['text'])))

    if listam:
        plate_list.append(listam)
    else:
        listam = re.findall(plate2_regex, ' '.join(list(up['text'])))
        if listam:
            plate_list.append(listam)

    return plate_list


def invoice_vehicle(df_func, vehicle_list):
    """
    Custom structures for vehicle number in the invoices

    Arguments:
    df -- pandas dataframe, a dataframe which contain information of the invoice
    vehicle_list -- list, values of vehicle numbers in invoice

    Return:
    vehicle_list -- list, values of vehicle numbers in invoice
    """

    new_df = df_func.copy()
    vehicle_regex = '[A-Z0-9]{16,17}'
    up = new_df[new_df['u-d'] == 0]

    listam = re.findall(vehicle_regex, ' '.join(list(up['text'])))

    if listam:
        vehicle_list.append(listam)

    return vehicle_list


def invoice_bank(df_func):
    """
    Return a list contain values for bank name.

    Arguments:
    df -- pandas dataframe, contain page information

    Return:
    banks -- list, bank names in page
    """
    banks = []
    new_df = df_func.copy()

    for index in range(len(new_df)):

        if 'sparkasse' in re.sub('[\W_]+', '', new_df['text'][index].lower()):

            banks.append(' '.join(list(new_df['text'][index:index + 2])))

        elif 'volksbank' in re.sub('[\W_]+', '', new_df['text'][index].lower()):

            banks.append(' '.join(list(new_df['text'][index:index + 2])))

    return banks


def invoice_iban(df_func):
    """
    Return a list contain values for iban.

    Arguments:
    df -- pandas dataframe, contain page information

    Return:
    iban_list -- list, contain iban values
    """

    # Define the required variables
    new_df = df_func.copy()
    iban_list = []
    remove_regex = '[^A-Za-z0-9\s\,]+'
    iban_regex = '(de[0-9]{2}[0-9]{4}\s[0-9]{4}\s[0-9]{4}\s[0-9]{4}\s[A-Za-z0-9]{2}' \
                 '|[A-Za-z0-9]{4}\s[0-9]{4}\s[0-9]{4}\s[0-9]{4}\s[0-9]{4}\s[A-Za-z0-9]{2}' \
                 '|[a-z]{2}\s[A-Za-z0-9]{4}\s[0-9]{4}\s[0-9]{4}\s[0-9]{4}\s[A-Za-z0-9]{4}' \
                 '|[a-z0-9]{22}' \
                 '|[A-Za-z0-9]{4}\s[A-Za-z0-9]{4}\s[A-Za-z0-9]{4}\s[A-Za-z0-9]{4}\s[A-Za-z0-9]{6})'

    # update the texts inside the dataframe
    new_df['text'] = new_df['text'].apply(lambda x: re.sub(remove_regex, '', x.lower()))

    # iterate over dataframe
    for i in range(1, len(new_df['text'])):

        # check if the word in dataframe is in synonym word dataframe
        if new_df['text'][i] == 'iban':
            # extract line for finding value
            val = new_df[i + 1:]
            line_text = ' '.join(list(val[val['line'] == new_df['line'][i]]['text']))

            iban = re.findall(iban_regex, line_text)

            # if the required value is not in the keyword line, then it is below the keyword
            if iban:
                iban_list.append(iban[0])

            else:
                iban = below_word(new_df, i, regex_pattern=iban_regex, column_or_line='line', num_word=0)  # find the
                # bellow value

                if iban:
                    iban_list.append(iban)

    if iban_list:
        return iban_list
    else:
        return []


def invoice_bic(df_func):
    """
    Return a list contain values for bic.

    Arguments:
    df -- pandas dataframe, contain page information

    Return:
    bic_list -- list, contain bic values
    """

    # Define the required variables
    new_df = df_func.copy()
    bic_list = []
    remove_regex = '[^A-Za-z0-9\s\,]+'
    bic_regex = '([a-z0-9]{11}|[a-z0-9]{8})'

    # update the texts inside the dataframe
    new_df['text'] = new_df['text'].apply(lambda x: re.sub(remove_regex, '', x.lower()))

    # iterate over dataframe
    for i in range(1, len(new_df['text'])):

        # check if the word in dataframe is in synonym word dataframe
        if new_df['text'][i] in ['bic', 'swiftbic', 'bicswift']:
            # extract line for finding value
            val = new_df[i + 1:]
            line_text = ' '.join(list(val[val['line'] == new_df['line'][i]]['text']))

            bic = re.findall(bic_regex, line_text)

            # if the required value is not in the keyword line, then it is below the keyword
            if bic:
                bic_list.append(bic[0])

            else:
                bic = below_word(new_df, i, regex_pattern=bic_regex, column_or_line='line',
                                 num_word=0)  # find the bellow value

                if bic:
                    bic_list.append(bic)

    if bic_list:
        return bic_list
    else:
        return []


def invoice_net(df_func, syns_df):
    """
    Return a list contain values for total net.

    Arguments:
    df -- pandas dataframe, contain page information
    syns_df -- pandas dataframe, a dataframe contain synonym words

    Return:
    net_list -- list, contain values for total net
    """

    # Define the required variables
    new_df = df_func.copy()
    syns_df['total net'] = syns_df['total net'].apply(str)
    nets = list(syns_df['total net'].drop([10]))
    net_list = []
    remove_pattern = '[^A-Za-z0-9\,\s]+'
    sell_pattern = '\d{2,6}\,\d{1,2}'

    # update the texts inside the dataframe
    new_df['text'] = new_df['text'].apply(lambda x: re.sub(remove_pattern, '', x.lower()))

    # remove the special characters from synonym words
    aaa = [re.sub('[\W_]+', '', word.lower()) for word in nets]

    # iterate over dataframe
    for i in range(1, len(new_df['text'])):

        # check if the word in dataframe is in synonym word dataframe
        if new_df['text'][i] in aaa or new_df['text'][i - 1] + new_df['text'][i] in aaa:
            if new_df['text'][i] in aaa:
                j = i
            else:
                j = i - 1

            # extract line for finding value
            val = new_df[j:]
            line_text = ' '.join(list(val[val['line'] == new_df['line'][i]]['text']))

            total = re.findall(sell_pattern, line_text)

            # if the required value is not in the keyword line, then it is below the keyword
            if total:
                net_list.append(total[0])

            else:
                total = below_word(new_df, j, sell_pattern)  # find the bellow value

                if total:
                    net_list.append(total)
                else:
                    total = below_word(new_df, j, '\d{2,6}\d{1,2}')  # find the bellow value

                    if total:
                        net_list.append(total)

    if net_list:
        return net_list
    else:
        return []


def invoice_tax(df_func, syns_df):
    """
    Return a list contain values for tax.

    Arguments:
    df -- pandas dataframe, contain page information
    syns_df -- pandas dataframe, a dataframe contain synonym words

    Retrun:
    tax_list -- list, contain tax values
    """

    # Define the required variables
    new_df = df_func.copy()
    syns_df['tax'] = syns_df['tax'].apply(str)
    taxs = list(syns_df['tax'].dropna())
    tax_list = []
    remove_pattern = '[^A-Za-z0-9\s\,\٪]+'
    tax_pattern = '(\d{2,6}\,\d{1,2}|\d{5,7})'

    # update the texts inside the dataframe
    new_df['text'] = new_df['text'].apply(lambda x: re.sub(remove_pattern, '', x.lower()))

    # remove the special characters from synonym words
    aaa = [re.sub(remove_pattern, '', word.lower()) for word in taxs]

    # iterate over dataframe
    for i in range(1, len(new_df['text'])):

        # check if the word in dataframe is in synonym word dataframe
        if re.sub('[\W_]+', '', new_df['text'][i]) in aaa or re.sub('[\W_]+', '',
                                                                    new_df['text'][i - 1] + new_df['text'][i]) in aaa:

            if re.sub('[\W_]+', '', new_df['text'][i]) in aaa:
                j = i
            else:
                j = i - 1

            if new_df['text'][i] != 'nan':

                # extract line for finding value
                val = new_df[j:]
                line_text = ' '.join(list(val[val['line'] == new_df['line'][i]]['text']))

                total = re.findall(tax_pattern, line_text)

                # if the required value is not in the keyword line, then it is below the keyword
                if total:
                    tax_list.append(total[-1])

                else:
                    total = below_word(new_df, j, tax_pattern, column_or_line='line')  # find the bellow value

                    if total:
                        tax_list.append(total)
                        total = below_word(new_df, j, '\d{2,6}\d{1,2}')  # find the bellow value

                        if total:
                            tax_list.append(total)

    if tax_list:
        if tax_list[0] == '19,00':
            tax_list.remove(tax_list[0])
        return tax_list
    else:
        return []


def invoice_total(df_func, syns_df):
    """
    Return a list contain values for total cost.

    Arguments:
    df -- pandas dataframe, contain page information
    syns_df -- pandas dataframe, a dataframe contain synonym words

    Retrun:
    total -- list, contain total values
    """

    # Define the required variables
    new_df = df_func.copy()
    syns_df['total amount'] = syns_df['total amount'].apply(str)
    syns_df = syns_df.drop(1)
    costs = list(syns_df['total amount'])
    cost_list = []
    remove_pattern = '[^A-Za-z0-9\s\,]+'
    cost_pattern = '(\d{2,6}\,\d{1,2}|\d{5,7})'

    # update the texts inside the dataframe
    new_df['text'] = new_df['text'].apply(lambda x: re.sub(remove_pattern, '', x.lower()))

    # remove the special characters from synonym words
    aaa = [re.sub(remove_pattern, '', word.lower()) for word in costs]

    # iterate over dataframe
    for i in range(1, len(new_df['text'])):

        # check if the word in dataframe is in synonym word dataframe
        if new_df['text'][i] in aaa or new_df['text'][i - 1] + new_df['text'][i] in aaa:
            if new_df['text'][i] in aaa:
                j = i
            else:
                j = i - 1

            if new_df['text'][i] == 'endpreis':

                total = below_word(new_df, j, cost_pattern, num_word=-1, depth=1000)

                if total:
                    cost_list.append(total)

            else:

                # extract line for finding value
                val = new_df[j:]
                line_text = ' '.join(list(val[val['line'] == new_df['line'][i]]['text']))

                total = re.findall(cost_pattern, line_text)

                # if the required value is not in the keyword line, then it is below the keyword
                if total:
                    cost_list.append(total[-1])

                else:
                    total = below_word(new_df, j, cost_pattern)  # find the bellow value

                    if total:
                        cost_list.append(total)
                    else:
                        total = below_word(new_df, j, '\d{2,6}')  # find the bellow value

                        if total:
                            cost_list.append(total)

    if cost_list:
        return cost_list
    else:
        return []


# def invoice_accuracy(kw, file, ref_dir):
#     """
#     Determine accuracy of extracted data from each invoice.
#
#     Arguments:
#     kw -- dictionary, dictionary contain invoice keywords.
#     file -- string, name of the file for reading json file.
#     ref_dir -- string, path to the reference json files.
#
#     Return:
#     acc -- integer, accuracy of the invoice.
#     """
#     tru = 0
#     total = 0
#
#     # open both extracted and reference json
#     with open(os.path.join(ref_dir, file + '.json'), 'r') as json1:
#         dic1 = json.load(json1)
#
#     for item in dic1.keys():
#
#         if type(kw[item]) is list and type(dic1[item]) is list:
#             for item in dic2[keyword]:
#                 temp_total += 1
#
#                 for item1 in dic1[keyword]:
#                     if difflib.SequenceMatcher(None, item, item1.lower()).ratio() > 0.80:
#                         temp_tru += 1
#                         dic1[keyword].remove(item1)
#
#             if temp_tru / temp_total > 0.7:
#                 tru += 1
#
#         elif type(dic2[keyword]) is list and type(dic1[keyword]) is not list:
#
#             for item in dic2[keyword]:
#                 temp_total += 1
#
#                 if difflib.SequenceMatcher(None, item, dic1[keyword].lower()).ratio() > 0.80:
#                     temp_tru += 1
#                     dic2[keyword].remove(item)
#
#             if temp_tru / temp_total > 0.7:
#                 tru += 1
#
#         elif type(dic1[keyword]) is list and type(dic2[keyword]) is not list:
#
#             for item in dic1[keyword]:
#                 temp_total += 1
#
#                 if difflib.SequenceMatcher(None, item, dic2[keyword].lower()).ratio() > 0.80:
#                     temp_tru += 1
#                     dic1[keyword].remove(item)
#
#             if temp_tru / temp_total > 0.7:
#                 tru += 1
#
#         else:
#             # calculate the accuracy of the extracted information
#             if difflib.SequenceMatcher(None, kw[item], dic1[item]).ratio() > 0.80:
#                 tru += 1
#
#         total += 1
#
#     acc = float(tru / total)
#
#     return acc


def find_values(df_list, pdf_file):
    """
    Finds values of given keywords in invoices and pass the values to another function for converting to json.

    Arguments:
    pdf_dir -- string, path to the pdf files want to read.
    syns_df -- pandas dataframe, contain given synonyms.
    ref_dir -- string, path to the reference json files.
    """

    # define variable which reset over each folder
    name_address = []
    workshop_list = []
    date = 'NO VALUE!'
    number_list = []
    total_list = []
    plate_list = []
    vehicle_list = []
    net_list = []
    iban_list = []
    bic_list = []
    bank_list = []
    tax_list = []

    syns_df = synonyms.transpose()

    for df_main in df_list:

        df = df_main.copy()

        # extract name and address list
        if list(df_main['text']) == list(df_list[0]['text']):
            name_address, workshop_list = invoice_name(df)

        # extract plate of the invoice
        plate_list = invoice_plate(df, plate_list)

        # extract date of the invoice
        if date == 'NO VALUE!':
            date = invoice_date(df, syns_df)
        else:
            pass

        # extract number of the invoice
        number_list.append(invoice_number(df, syns_df))

        # extract vehicle number
        vehicle_list = invoice_vehicle(df, vehicle_list)

        # extract bank names
        bank_list.append(invoice_bank(df))

        # extract iban and bic number of the invoices
        iban_list.append(invoice_iban(df))
        bic_list.append(invoice_bic(df))

        # extract information of the total net
        net_list.append(invoice_net(df, syns_df))

        # extract information of the tax
        tax_list.append(invoice_tax(df, syns_df))

        # extract information of the total cost
        total_list.append(invoice_total(df, syns_df))

    # Update total amount of the invoice after each folder
    try:
        total = [i for i in total_list if i][-1][-1]
    except IndexError:
        total = 'NO VALUE!'

    try:
        number_list = [i.upper() for i in number_list if i]
        number = number_list[0]
    except IndexError:
        number = "NO VALUE!"

    try:
        bank_list = [i for i in bank_list if i]
        bank = bank_list[-1]
        if len(bank) == 1:
            bank_1, bank_2, bank_3 = bank[0], 'NO VALUE!', 'NO VALUE!'
        elif len(bank) == 2:
            bank_1, bank_2, bank_3 = bank[0], bank[1], 'NO VALUE!'
        elif len(bank) > 2:
            bank_1, bank_2, bank_3 = bank[0], bank[1], bank[2]
    except IndexError:
        bank_1, bank_2, bank_3 = 'NO VALUE!', 'NO VALUE!', 'NO VALUE!'

    try:
        iban_list = [i for i in iban_list if i]
        if len(iban_list[-1]) == 1:
            iban_1, iban_2, iban_3 = iban_list[-1][0].upper(), 'NO VALUE!', 'NO VALUE!'

            if bool(re.search(r'\d', iban_1)):
                pass
            else:
                iban_1 = 'NO VALUE!'
        else:
            iban = iban_list[-1]
            for item in iban:
                if bool(re.search(r'\d', item)):
                    continue
                else:
                    iban.remove(item)

            if len(iban) == 2:
                iban_1, iban_2, iban_3 = iban[0].upper(), iban[1].upper(), 'NO VALUE!'

            elif len(iban) > 2:
                iban_1, iban_2, iban_3 = iban[0].upper(), iban[1].upper(), iban[2].upper()

    except IndexError:
        iban_1, iban_2, iban_3 = 'NO VALUE!', 'NO VALUE!', 'NO VALUE!'

    try:
        bic_list = [i for i in bic_list if i]
        bic_list = [i.upper() for i in bic_list[-1]]
        if len(bic_list) == 1:
            bic_1, bic_2, bic_3 = bic_list[0], 'NO VALUE!', 'NO VALUE!'
        elif len(bic_list) == 2:
            bic_1, bic_2, bic_3 = bic_list[0], bic_list[1], 'NO VALUE!'
        elif len(bic_list) > 3:
            bic_1, bic_2, bic_3 = bic_list[0], bic_list[1], bic_list[2]
        else:
            bic_1, bic_2, bic_3 = 'NO VALUE!', 'NO VALUE!', 'NO VALUE!'
    except IndexError:
        bic_1, bic_2, bic_3 = 'NO VALUE!', 'NO VALUE!', 'NO VALUE!'

    try:
        plate = plate_list[0][0]
    except IndexError:
        plate = 'NO VALUE!'

    try:
        vehicle = vehicle_list[0][0]
    except IndexError:
        vehicle = 'NO VALUE!'

    try:
        net = [i for i in net_list if i][-1][0]
    except IndexError:
        net = 'NO VALUE!'

    try:
        tax = tax_list[-1][0]
    except IndexError:
        tax = 'NO VALUE!'

    if name_address:
        if type(name_address[0]) is list:
            name = name_address[0]
        else:
            name = name_address

        name = [i for i in name if len(i.split()[0]) > 1]
        try:
            VN_Name, VN_Strasse, VN_PLZ, VN_Ort = ' '.join(name[:-2]), name[-2] \
                , name[-1].split()[0], ' '.join(name[-1].split()[1:])
        except IndexError:
            VN_Name, VN_Strasse, VN_PLZ, VN_Ort = 'NO VALUE!', 'NO VALUE!', 'NO VALUE!', 'NO VALUE!'
    else:
        VN_Name, VN_Strasse, VN_PLZ, VN_Ort = 'NO VALUE!', 'NO VALUE!', 'NO VALUE!', 'NO VALUE!'

    if not workshop_list:
        workshop_list = 'NO VALUE!'

    # Assign values to the final dictionary
    kw = {'Werkstatt': workshop_list, 'VN_Name': VN_Name, 'VN_Strasse': VN_Strasse, 'VN_PLZ': VN_PLZ, 'VN_Ort': VN_Ort
        , 'Rechnungs_Datum': date, 'Rechnung_Nr': number, 'FIN': vehicle, 'amtl_Kennzeichen': plate
        , 'Bank_1': bank_1, 'Bank_2': bank_2, 'Bank_3': bank_3, 'IBAN_1': iban_1, 'IBAN_2': iban_2, 'IBAN_3': iban_3
        , 'BIC_1': bic_1, 'BIC_2': bic_2, 'BIC_3': bic_3, 'Rechnung_Netto': net, 'Rechnung_UST': tax
        , 'Rechnung_Brutto': total}

    # if ref_dir:  # calculate the accuracy of each file
    #     accuracy = invoice_accuracy(kw, folder, ref_dir)
    #     kw['accuracy'] = accuracy

    return kw

# if ref_dir: # calculate the accuracy of all files
#     json_accuracy(pdf_dir, kw, ref_dir)
