# Import libraries
from operator import itemgetter
from cv2 import cv2
import pandas as pd
import tr
import re
import os

from utils.constants import invalid_list_revision
from configures import configs


def tr_extraction(pdf_file, page):
    """
    Use TrOCR for page
    Args:
        pdf_file: string, name of the pdf file
        page: string, number of the page in string

    Returns:
        df: pandas dataframe, dataframe contain tr information
    """

    if page <= 9:  # name each page after number of pdf file page
        page_number = f'00{page}'
    elif page <= 99:
        page_number = f'0{page}'
    else:
        page_number = f'{page}'

    revision_main_path = configs['revision_file_path_for_tr_extraction']

    revision_temp_folder = os.path.join(revision_main_path, pdf_file[:-4])

    revision_page_path = os.path.join(revision_temp_folder, f'PP_page_{page_number}.jpeg')
    revision_page_path_noPP = os.path.join(revision_temp_folder, f'page_{page_number}.jpeg')

    df = pd.DataFrame(columns=['text', 'left', 'top', 'width', 'height', 'conf'])

    image = cv2.imread(revision_page_path_noPP, cv2.IMREAD_GRAYSCALE)

    tr_info = tr.run(revision_page_path)

    if len(tr_info) < 10:
        return False

    # iterate over returned values from tr ocr
    for i in range(len(tr_info)):

        if tr_info[i][1] == '':
            continue
        else:
            pass

        # extract the location of texts
        (cor_list, t, c) = (tr_info[i])
        [x, y, w, h, _] = cor_list

        df = df.append({'text': t,
                        'left': int(x),
                        'top': int(y),
                        'width': int(w),
                        'height': int(h),
                        'conf': c},
                       ignore_index=True)

    return df, image


def remove_lines_between_gebaude(leftt_gebaude, rightt_gebaude, df):
    """
    Remove underlines

    Arguments:
    left_gebaude -- float, left border of gebaude.
    right_gebaude -- float, right border of gebaude.
    df -- pandas dataframe, contain information of all data in a page.

    Return:
    correct_df -- pandas dataframe, without underlines.
    """

    correct_df = df[df['text'] != '<LINE>']
    df_lines = df[df['text'] == '<LINE>']

    val = df_lines[(df_lines['left'] <= int(leftt_gebaude)) | (df_lines['left'] >= int(rightt_gebaude))]

    correct_df = correct_df.append(val, ignore_index=True)

    return correct_df


def vertical_lines(df):
    """
    Find the vertical lines for each column

    Arguments:
    df -- pandas dataframe, a dataframe contain information of the table

    Return:
    borders -- tuple, contain the values of left and right border for each column
    """

    left_pos = 0
    right_pos = 0
    left_gefahr = 0
    right_gefahr = 0
    left_mangel = 0
    right_mangel = 0
    left_gebaude = 0
    right_gebaude = 0
    left_betriebs = 0
    right_betriebs = 0

    for index in range(len(df)):

        # _____________________________________________________________________________________________________________
        # Find the borders for "lfd" and "gefahr" keywords
        # _____________________________________________________________________________________________________________
        if (re.sub('[\W_]+', '', df['text'][index].lower()) == 'gefahr' or
            re.sub('[\W_]+', '', df['text'][index].lower()) == 'ge' or
            re.sub('[\W_]+', '', df['text'][index].lower()) == 'gefah' or
            re.sub('[\W_]+', '', df['text'][index].lower()) == 'gef' or
            re.sub('[\W_]+', '', df['text'][index].lower()) == 'fahr') and \
                left_gefahr == 0:

            if 'sowie' in re.sub('[\W_]+', '', ' '.join(list(df[df['line'] == df['line'][index]]['text'])).lower()) or \
                    'sowie' in re.sub('[\W_]+', '',
                                      ' '.join(list(df[df['line'] == df['line'][index] - 1]['text'])).lower()) or \
                    'anlage' in re.sub('[\W_]+', '',
                                       ' '.join(list(df[df['line'] == df['line'][index] + 1]['text'])).lower()) or \
                    'anlage' in re.sub('[\W_]+', '',
                                       ' '.join(list(df[df['line'] == df['line'][index]]['text'])).lower()):
                left_gefahr = df['left'][index] - int(df['width'][index] / 2) - 3
                right_gefahr = df['left'][index] + int(df['width'][index] / 2) + 1
        # _____________________________________________________________________________________________________________
        # Find the borders for "pos" keyword
        # _____________________________________________________________________________________________________________
        elif re.sub('[\W_]+', '', df['text'][index].lower()) == 'pos' and left_pos == 0:

            if 'sowie' in re.sub('[\W_]+', '', ' '.join(list(df[df['line'] == df['line'][index]]['text'])).lower()) or \
                    'sowie' in re.sub('[\W_]+', '',
                                      ' '.join(list(df[df['line'] == df['line'][index] - 1]['text'])).lower()) or \
                    'anlage' in re.sub('[\W_]+', '',
                                       ' '.join(list(df[df['line'] == df['line'][index] + 1]['text'])).lower()) or \
                    'anlage' in re.sub('[\W_]+', '',
                                       ' '.join(list(df[df['line'] == df['line'][index]]['text'])).lower()):
                left_pos = df['left'][index] - int(df['width'][index] / 2) - 9
                right_pos = df['left'][index] + int(df['width'][index] / 2) + 8
        # _____________________________________________________________________________________________________________
        # Find the borders for "gebaude" keyword
        # _____________________________________________________________________________________________________________
        # elif re.sub('[\W_]+', '', df['text'][index].lower()) == 'gebäude' and \
        #         'anlage' in re.sub('[\W_]+', '',
        #                            ' '.join(list(df[df['line'] == df['line'][index] + 1]['text'])).lower()) and \
        #         'raum' in re.sub('[\W_]+', '',
        #                          ' '.join(list(df[df['line'] == df['line'][index] + 2]['text'])).lower()) \
        #         and left_gebaude == 0:
        #
        #     left_gebaude = df['left'][index] - int(df['width'][index] / 2) - 9
        #     right_gebaude = df['left'][index] + int(df['width'][index] / 2) + 35
        # _____________________________________________________________________________________________________________
        # Find the borders for "mangel" keyword
        # _____________________________________________________________________________________________________________
        elif (re.sub('[\W]+', '', df['text'][index].lower()) == 'mangel' or
              re.sub('[\W]+', '', df['text'][index].lower()) == 'nummer') and left_mangel == 0:

            if 'sowie' in re.sub('[\W_]+', '', ' '.join(list(df[df['line'] == df['line'][index]]['text'])).lower()) or \
                    'sowie' in re.sub('[\W_]+', '',
                                      ' '.join(list(df[df['line'] == df['line'][index] - 1]['text'])).lower()) or \
                    'nummer' in re.sub('[\W_]+', '',
                                       ' '.join(list(df[df['line'] == df['line'][index] + 1]['text'])).lower()) or \
                    re.sub('[\W]+', '', df['text'][index + 1].lower()) == 'betriebs':
                left_mangel = df['left'][index] - int(df['width'][index] / 2) - 15
                right_mangel = df['left'][index] + int(df['width'][index] / 2) + 5
        # _____________________________________________________________________________________________________________
        # Find the borders for "betriebs" keyword
        # _____________________________________________________________________________________________________________
        elif (re.sub('[\W]+', '', df['text'][index].lower()) == 'betriebs' or
              re.sub('[\W]+', '', df['text'][index].lower()) == 'bereich') and left_betriebs == 0:

            if 'sowie' in re.sub('[\W_]+', '', ' '.join(list(df[df['line'] == df['line'][index]]['text'])).lower()) or \
                    'sowie' in re.sub('[\W_]+', '',
                                      ' '.join(list(df[df['line'] == df['line'][index] - 1]['text'])).lower()) or \
                    'anlage' in re.sub('[\W_]+', '',
                                       ' '.join(list(df[df['line'] == df['line'][index] + 1]['text'])).lower()) or \
                    'anlage' in re.sub('[\W_]+', '',
                                       ' '.join(list(df[df['line'] == df['line'][index]]['text'])).lower()):
                left_betriebs = df['left'][index] - int(df['width'][index] / 2) - 8
                right_betriebs = df['left'][index] + int(df['width'][index] / 2) + 15

    borders = (left_gefahr, right_gefahr, left_gebaude, right_gebaude, left_pos,
               right_pos, left_mangel, right_mangel, left_betriebs, right_betriebs)

    return borders


def vertical_lines_plus(df, df_tr, pdf_file, page):
    """
    Find vertical lines of the image.

    Args:
        df: pandas dataframe, contain information.
        df_tr: pandas dataframe, contain information from tr
        pdf_file: string, name of the pdf file.
        page: string, number of the page in string.

    Returns:
        borders: list, contain borders of columns.
    """
    left_pos = 0
    right_pos = 0
    left_gefahr = 0
    right_gefahr = 0
    left_mangel = 0
    right_mangel = 0
    left_gebaude = 0
    right_gebaude = 0
    left_betriebs = 0
    right_betriebs = 0

    # Read image of the current page
    if page <= 9:  # name each page after number of pdf file page
        page_number = f'00{page}'
    elif page <= 99:
        page_number = f'0{page}'
    else:
        page_number = f'{page}'

    revision_main_path = configs['revision_file_path_for_tr_extraction']

    revision_temp_folder = os.path.join(revision_main_path, pdf_file[:-4])

    revision_page_path = os.path.join(revision_temp_folder, f'page_{page_number}.jpeg')

    img = cv2.imread(revision_page_path)

    # Find headers of the table for line verification
    try:
        y_raum = int(list(df_tr[(df_tr['text'].str.contains('Raum')) |
                                (df_tr['text'].str.contains('Gebaude')) |
                                (df_tr['text'].str.contains('Gebäude')) |
                                (df_tr['text'].str.contains('empfohlene'))]['top'])[0])
    except IndexError:
        y_raum = 520

    line_list = []

    if type(img) is str:
        img = cv2.imread(img)

    image = img.copy()

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

    # create a kernel to find lines
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 25))
    # detect lines with created kernel
    detected_horizontal = cv2.morphologyEx(otsu, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
    # find horizontal contours of the image
    cnts_hor = cv2.findContours(detected_horizontal, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # draw white lines on detected lines to cover them
    cnts_ho = cnts_hor[0] if len(cnts_hor) == 2 else cnts_hor[1]

    # Only save contours that pass the headers of the table
    for c in cnts_ho:
        [x1, y1], [_, _] = c[0][0], c[1][0]
        length = cv2.arcLength(c, True)
        if y1 < y_raum + 10 < y1 + int(length / 2):
            line_list.append([x1, y1])

    # Sort founded lines base on left to right in the image
    sort_lines = sorted(line_list, key=itemgetter(0))

    # Iterate over lines and find the words between two lines.
    for vert_line in range(1, len(sort_lines)):

        val = df[(df['left'] > sort_lines[vert_line - 1][0]) & (df['left'] < sort_lines[vert_line][0])]
        val_tr = df_tr[(df_tr['left'] > sort_lines[vert_line - 1][0]) & (df_tr['left'] < sort_lines[vert_line][0])]
        # _____________________________________________________________________________________________________________
        # Find the borders for "lfd" and "gefahr" keywords
        # _____________________________________________________________________________________________________________
        if list(val[(val['text'].str.contains('gefahr')) |
                    (val['text'].str.contains('Gef.')) |
                    (val['text'].str.contains('Gefahr')) |
                    (val['text'].str.contains('Ge-')) |
                    (val['text'].str.contains('Gefah')) |
                    (val['text'].str.contains('Getanr'))]['text']) and \
                not list(val[val['text'].str.contains('Raum')]['text']) and \
                not left_gefahr:
            left_gefahr = sort_lines[vert_line - 1][0]
            right_gefahr = sort_lines[vert_line][0]

        # _____________________________________________________________________________________________________________
        # Find the borders for "pos" keywords
        # _____________________________________________________________________________________________________________
        elif list(val[(val['text'].str.contains('Pos'))]['text']) and \
                not list(val[val['text'].str.contains('Raum')]['text']) and \
                not left_pos:
            left_pos = sort_lines[vert_line - 1][0]
            right_pos = sort_lines[vert_line][0]

        # _____________________________________________________________________________________________________________
        # Find the borders for "gebaude" keywords
        # _____________________________________________________________________________________________________________
        elif list(val_tr[(val_tr['text'].str.contains('Anlage')) |
                         (val_tr['text'].str.contains('Gebaude')) |
                         (val_tr['text'].str.contains('Gebäude')) |
                         (val_tr['text'].str.contains('Raum'))]['text']) and not left_gebaude:
            left_gebaude = sort_lines[vert_line - 1][0]
            right_gebaude = sort_lines[vert_line][0]

        # _____________________________________________________________________________________________________________
        # Find the borders for "mangel" keywords
        # _____________________________________________________________________________________________________________
        elif list(val_tr[(val_tr['text'].str.contains('Mangel')) |
                         (val_tr['text'].str.contains('Nummer')) |
                         (val_tr['text'].str.contains('nummer'))]['text']) \
                and not list(val_tr[(val_tr['text'].str.contains('empfohlene')) |
                                    (val_tr['text'].str.contains('Anlage'))]['text']) and not left_mangel:
            left_mangel = sort_lines[vert_line - 1][0]
            right_mangel = sort_lines[vert_line][0]

        # _____________________________________________________________________________________________________________
        # Find the borders for "Betriebs" keywords
        # _____________________________________________________________________________________________________________
        elif list(val_tr[(val_tr['text'].str.contains('Betriebs')) |
                         (val_tr['text'].str.contains('Betr.')) |
                         (val_tr['text'].str.contains('Bereich')) |
                         (val_tr['text'].str.contains('bereich'))]['text']) \
                and not list(val_tr[(val_tr['text'].str.contains('empfohlene')) |
                                    (val_tr['text'].str.contains('Anlage')) |
                                    (val_tr['text'].str.contains('Angabe'))]['text']) and not left_betriebs:
            left_betriebs = sort_lines[vert_line - 1][0]
            right_betriebs = sort_lines[vert_line][0]

    borders = (left_gefahr, right_gefahr, left_gebaude - 2, right_gebaude, left_pos,
               right_pos, left_mangel, right_mangel, left_betriebs, right_betriebs)

    return borders


def extract_boxes(df, borders, c_lines, df_tr, image):
    """
    extract the values in each box.

    Arguments:
    df -- pandas dataframe, contain information of table.
    borders -- tuple, contain borders of each column.
    c_lines -- list, contain horizontal lines in table.

    Return:
    data_list -- list, contain extracted information of each box
    """

    (left_gefahr, right_gefahr, left_gebaude, right_gebaude, left_pos,
     right_pos, left_mangel, right_mangel, left_betriebs, right_betriebs) = borders

    data_list = []

    # Iterate over horizontal lines and extract texts in each box
    for line in range(1, len(c_lines)):

        row_list = []

        # _____________________________________________________________________________________________________________
        # Extract texts in box for "lfd" keyword
        # _____________________________________________________________________________________________________________
        if left_gefahr:
            val = df_tr[(df_tr['left'] < left_gefahr) & (df_tr['left'] > left_gefahr - 100)]
            val1 = val[val['top'] > c_lines[line - 1]]
            box = val1[val1['top'] < c_lines[line]]

            if list(box['text']):
                row_list.append(' '.join(list(box[box['conf'] * 100 > 75]['text'])))
            else:
                row_list.append('')
        else:
            row_list.append('')
        # _____________________________________________________________________________________________________________
        # Extract texts in box for "gefahr" keyword
        # _____________________________________________________________________________________________________________
        if right_gefahr and left_gefahr:
            val = df[df['left'] > left_gefahr]
            val1 = val[val['left'] < right_gefahr]
            val2 = val1[val1['top'] > c_lines[line - 1]]
            box = val2[val2['top'] < c_lines[line]]

            if list(box['text']):
                row_list.append(' '.join(list(box[box['conf'] * 100 > 75]['text'])))
            else:
                row_list.append('')
        else:
            row_list.append('')
        # _____________________________________________________________________________________________________________
        # Extract texts in box for "pos" keyword
        # _____________________________________________________________________________________________________________
        if left_pos and right_pos:
            val = df_tr[df_tr['left'] > left_pos]
            val1 = val[val['left'] < right_pos]
            val2 = val1[val1['top'] > c_lines[line - 1]]
            box = val2[val2['top'] < c_lines[line]]

            if list(box['text']):
                row_list.append(' '.join(list(box[box['conf'] * 100 > 75]['text'])))
            else:
                row_list.append('')
        else:
            row_list.append('')
        # _____________________________________________________________________________________________________________
        # Extract texts in box for "gebaude" keyword between "pos" and "mangel" or between "gefahr" and "mangel"
        # _____________________________________________________________________________________________________________
        if left_gebaude and right_gebaude:
            val = df[df['left'] > left_gebaude]
            val1 = val[val['left'] < right_gebaude]
            val2 = val1[val1['top'] > c_lines[line - 1]]
            box = val2[val2['top'] < c_lines[line]].reset_index()

            # lows = box[box['conf'] < 75].reset_index()
            main_text = ''

            for i, kalame in enumerate(box['text']):

                if box['conf'][i] < 75:
                    cv2.imwrite(f'./{i}.jpeg',
                                image[int(box['top'][i] - box['height'][i]/2 - 2):
                                      int(box['top'][i] + box['height'][i]/2 + 2),
                                      int(box['left'][i] - box['width'][i]/2 - 2):
                                      int(box['left'][i] + box['width'][i]/2 + 2)])

                    tr_info = tr.run(f'./{i}.jpeg')

                    os.remove(f'./{i}.jpeg')

                    if tr_info:
                        tr_word = tr_info[-1][1]
                        a = ['ö', 'Ö', 'ä', 'Ä', 'ü', 'Ü']
                        b = ['o', 'O', 'a', 'A', 'u', 'U']
                        kalame_jadid = ''.join([char if char not in a else b[a.index(char)] for char in kalame])
                        if kalame_jadid == tr_word:
                            final_word = kalame
                        else:
                            final_word = tr_word

                        word = final_word
                    else:
                        word = kalame

                    main_text = main_text + ' ' + word

                else:
                    main_text = main_text + ' ' + kalame

            if list(box['text']):
                row_list.append(main_text.strip())
            else:
                row_list.append('')

        elif right_pos and left_mangel:
            val = df_tr[df_tr['left'] > right_pos]
            val1 = val[val['left'] < left_mangel]
            val2 = val1[val1['top'] > c_lines[line - 1]]
            box = val2[val2['top'] < c_lines[line]]

            if list(box['text']):
                row_list.append(' '.join(list(box[box['conf'] > 75]['text'])))
            else:
                row_list.append('')

        elif right_gefahr and left_mangel:
            val = df_tr[df_tr['left'] < left_mangel]
            val1 = val[val['left'] > right_gefahr]
            val2 = val1[val1['top'] > c_lines[line - 1]]
            box = val2[val2['top'] < c_lines[line]]

            if list(box['text']):
                row_list.append(' '.join(list(box[box['conf'] > 75]['text'])))
            else:
                row_list.append('')
        else:
            row_list.append('')
        # _____________________________________________________________________________________________________________
        # Extract texts in box for "mangel" keyword
        # _____________________________________________________________________________________________________________
        if left_mangel and right_mangel:
            val = df_tr[df_tr['left'] > left_mangel]
            val1 = val[val['left'] < right_mangel]
            val2 = val1[val1['top'] > c_lines[line - 1]]
            box = val2[val2['top'] < c_lines[line]]

            if list(box['text']):
                row_list.append(' '.join(list(box[box['conf'] * 100 > 75]['text'])))
            else:
                val_ = df[df['left'] > left_mangel]
                val1_ = val_[val_['left'] < right_mangel]
                val2_ = val1_[val1_['top'] > c_lines[line - 1]]
                box_ = val2_[val2_['top'] < c_lines[line]]

                if list(box_['text']):
                    row_list.append(' '.join(list(box_[box_['conf'] * 100 > 75]['text'])))
                else:
                    row_list.append('')
        else:
            row_list.append('')
        # _____________________________________________________________________________________________________________
        # Extract texts in box for "betriebs" keyword
        # _____________________________________________________________________________________________________________
        if left_betriebs and right_betriebs:
            val = df_tr[df_tr['left'] > left_betriebs]
            val1 = val[val['left'] < right_betriebs]
            val2 = val1[val1['top'] > c_lines[line - 1]]
            box = val2[val2['top'] < c_lines[line]]

            if list(box['text']):
                row_list.append(' '.join(list(box[box['conf'] * 100 > 75]['text'])))
            else:
                val_ = df[df['left'] > left_betriebs]
                val1_ = val_[val_['left'] < right_betriebs]
                val2_ = val1_[val1_['top'] > c_lines[line - 1]]
                box_ = val2_[val2_['top'] < c_lines[line]]

                if list(box_['text']):
                    row_list.append(' '.join(list(box_[box_['conf'] * 100 > 75]['text'])))
                else:
                    row_list.append('')
        else:
            row_list.append('')
        # _____________________________________________________________________________________________________________
        # _____________________________________________________________________________________________________________

        data_list.append(row_list)

    return data_list


def split_table(df_df, df_df_tr):
    """
    Split the table from document.

    Arguments:
    df-df -- pandas dataframe, contain information of document

    Return:
    df -- pandas dataframe, contain information of table
    """
    for index in range(len(df_df)):

        try:
            kalame_aval = re.sub('[^a-z0-9öäüß\s]+', '', df_df['text'][index].lower())
            kalame_dovom = re.sub('[^a-z0-9öäüß\s]+', '', df_df['text'][index + 1].lower())
            kalame_sevom = re.sub('[^a-z0-9öäüß\s]+', '', df_df['text'][index + 2].lower())
        except KeyError:
            kalame_aval = re.sub('[^a-z0-9öäüß\s]+', '', df_df['text'][index].lower())
            kalame_dovom = -1
            kalame_sevom = -1

        if kalame_aval == 'raum' and kalame_dovom == 'sowie':
            df = df_df[(df_df['top'] > df_df['top'][index] - 20) | (df_df['text'].str.contains('<LINE>'))].reset_index()
            df_tr = df_df_tr[df_df_tr['top'] > df_df['top'][index] - 20].reset_index()
            return df, df_tr

        elif kalame_aval == 'anlage' and kalame_dovom == 'raum':
            df = df_df[(df_df['top'] > df_df['top'][index] - 20) | (df_df['text'].str.contains('<LINE>'))].reset_index()
            df_tr = df_df_tr[df_df_tr['top'] > df_df['top'][index] - 20].reset_index()
            return df, df_tr

        elif kalame_aval == 'ifd' and kalame_dovom == 'nr' and kalame_sevom == 'gefahr':
            df = df_df[(df_df['top'] > df_df['top'][index] - 20) | (df_df['text'].str.contains('<LINE>'))].reset_index()
            df_tr = df_df_tr[df_df_tr['top'] > df_df['top'][index] - 20].reset_index()
            return df, df_tr

        elif kalame_aval == 'gefahr' and kalame_dovom == 'gebäude':
            df = df_df[(df_df['top'] > df_df['top'][index] - 20) | (df_df['text'].str.contains('<LINE>'))].reset_index()
            df_tr = df_df_tr[df_df_tr['top'] > df_df['top'][index] - 20].reset_index()
            return df, df_tr

        elif kalame_aval == 'gefahr' and kalame_dovom == 'gebaude':
            df = df_df[(df_df['top'] > df_df['top'][index] - 20) | (df_df['text'].str.contains('<LINE>'))].reset_index()
            df_tr = df_df_tr[df_df_tr['top'] > df_df['top'][index] - 20].reset_index()
            return df, df_tr

        elif kalame_aval == 'gebäude' and (kalame_dovom == 'raum' or kalame_sevom == 'raum'):
            df = df_df[(df_df['top'] > df_df['top'][index] - 20) | (df_df['text'].str.contains('<LINE>'))].reset_index()
            df_tr = df_df_tr[df_df_tr['top'] > df_df['top'][index] - 20].reset_index()
            return df, df_tr

    return df_df, df_df_tr


def approve_gebaude(gebaude):
    """
    Approve the gebaude values

    Arguments:
    gebaude -- string, texts of the gebaude keyword

    Return:
    approval -- bool, True of it is valid False of not
    """

    # define ignoring texts
    invalid_list = invalid_list_revision

    for invalid in invalid_list:
        if invalid.lower() in gebaude.lower():
            return 0

    if "allgemeine angaben" in gebaude.lower():
        return 2

    return 1


def fill_dictionary(data_list, poss=False):
    """
    Fill the output dictionary with data.

    Arguments:
        data_list: list, contain all data in tables in a document.
        poss: boolean, weather print bool or not

    Return:
        kw: dictionary, contain keywords and values.
    """

    kw = {}

    # After extracting data for each row and each keyword the program updates the output dictionary for each folder
    for i in range(1, len(data_list) + 1):

        for j in range(1, len(data_list[i - 1]) + 1):
            lfd = re.sub('[^0-9.]+', '', data_list[i - 1][j - 1][0].strip())
            gef = re.sub('[^oO0xX]+', '', data_list[i - 1][j - 1][1].strip()).upper().replace('0', 'O')
            gefahr = "".join(set(gef))
            pos = re.sub('[^0-9.]+', '', data_list[i - 1][j - 1][2].strip())
            gebaude = data_list[i - 1][j - 1][3].strip()
            mangel = re.sub('[^a-zA-Z0-9\söäüß./]+', '', data_list[i - 1][j - 1][4].strip())
            betriebs = re.sub('[^a-zA-Z0-9\sß.+]+', '', data_list[i - 1][j - 1][5].strip())

            if len(lfd) <= 1 and len(gefahr) <= 1 and len(pos) <= 1 and len(gebaude) <= 1 and len(
                    mangel) <= 1 and len(betriebs) <= 1:
                continue
            else:
                if approve_gebaude(gebaude) == 1:
                    if mangel and mangel.isdigit() and '0000' not in mangel:
                        ll = int(len(list((kw.keys()))) / 5 + 1)
                        kw[f'NR ({ll})'] = lfd
                        kw[f'Gefahr ({ll})'] = gefahr
                        if poss:
                            kw[f'Pos ({ll})'] = pos
                        else:
                            pass
                        kw[f'Gebäude ({ll})'] = gebaude
                        kw[f'Mangelnummer ({ll})'] = mangel
                        kw[f'Betriebsbereich ({ll})'] = betriebs
                    else:
                        continue
                elif approve_gebaude(gebaude) == 2:
                    return kw

    return kw


def find_values(df_list, pdf_file):
    """
    Find values in appendix of Revision documents and convert to json.

    Arguments:
        df_list: list, contain all dataframes in pdf file.
        pdf_file: string, name of the pdf file.
    """

    # define variable which need to be reset over each folder
    data_list = []
    fire = False
    perv_borders = []
    left_pos, right_pos = 0, 0

    # --------------------------------------------------------------------------------------------------------------
    # Iterate over each excel file in each folder
    for ii, df_df in enumerate(df_list):

        texts = ' '.join(list(df_df['text'])).lower()

        # find table from some specific keyword which occurs in most formats
        if 'raum sowie' in re.sub('[^a-z0-9\s]+', '', texts) or \
                'anlage raum' in re.sub('[^a-z0-9\s]+', '', texts) or \
                'ifd nr gefahr' in re.sub('[^a-z0-9\s]+', '', texts) or \
                'gefahr gebäude' in re.sub('[^a-z0-9öäüß\s]+', '', texts) or \
                'gefahr gebaude' in re.sub('[^a-z0-9\s]+', '', texts) or \
                'nummer bereich' in re.sub('[^a-z0-9\s]+', '', texts) or fire:

            df_tr, image = tr_extraction(pdf_file, ii + 1)

            # split the data in the table
            df_jadid, df_tr_jadid = split_table(df_df, df_tr)

            # after finding table the program give table to extract_boxes function and receives a list which
            # contain a list in number of rows in each page and in each list there is value for every keyword
            texts = ' '.join(list(df_jadid['text'])).lower()

            if 'raum sowie' in re.sub('[^a-z0-9\s]+', '', texts) or \
                    'anlage raum' in re.sub('[^a-z0-9\s]+', '', texts) or \
                    'ifd nr gefahr' in re.sub('[^a-z0-9\s]+', '', texts) or \
                    'gefahr gebäude' in re.sub('[^a-z0-9öäüß\s]+', '', texts) or \
                    'gefahr gebaude' in re.sub('[^a-z0-9\s]+', '', texts) or \
                    'nummer bereich' in re.sub('[^a-z0-9\s]+', '', texts):

                borders = vertical_lines_plus(df_jadid, df_tr_jadid, pdf_file, ii + 1)

                if borders.count(0) > 2:
                    borders = vertical_lines(df_jadid)

                if fire:
                    if borders[0] == 0 and borders[1] == 0:
                        borders = perv_borders

                    elif borders[-1] == 0 and borders[-2] == 0:
                        borders = perv_borders

                (left_gefahr, right_gefahr, left_gebaude, right_gebaude, left_pos,
                 right_pos, left_mangel, right_mangel, left_betriebs, right_betriebs) = borders

                if right_gebaude:
                    df = remove_lines_between_gebaude(left_gebaude, right_gebaude, df_jadid)
                else:
                    df = remove_lines_between_gebaude(right_gefahr, left_mangel, df_jadid)

                lines = list(df[df['text'] == '<LINE>']['top'])
                # c_lines = clean_lines(lines)
                a = extract_boxes(df, borders, lines, df_tr_jadid, image)
                data_list.append(a)

            else:
                borders = perv_borders

                (left_gefahr, right_gefahr, left_gebaude, right_gebaude, left_pos,
                 right_pos, left_mangel, right_mangel, left_betriebs, right_betriebs) = borders

                df = remove_lines_between_gebaude(left_gebaude, right_gebaude, df_jadid)

                lines = sorted(list(df[df['text'] == '<LINE>']['top']))
                # c_lines = clean_lines(lines)
                a = extract_boxes(df, borders, lines, df_tr, image)
                data_list.append(a)

            fire = True
            perv_borders = borders

    if left_pos and right_pos:
        kw = fill_dictionary(data_list, True)
    else:
        kw = fill_dictionary(data_list)

    return kw
