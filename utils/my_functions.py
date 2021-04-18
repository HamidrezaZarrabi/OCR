# Import libraries
import difflib
import imutils
from cv2 import cv2
import re


def imshow_fast(image, resize=1000):
    """
    Show the image fast

    Arguments:
        image: numpy array, image
        resize: bool or integer, if true the output image will be smaller to be seen
    """

    if resize:
        image = imutils.resize(image, height=resize)
    cv2.imshow("test", image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def rectangle_fast(image, df, index, color=(0, 255, 0)):
    """
    Draw a rectangle around a word in dataframes.

    Args:
        image: numpy array, image to draw rectangle on.
        df: pandas dataframe, contain all information of the page.
        index: integer, index of the word.
        color: tuple, determine color of rectangle
    """
    cv2.rectangle(image
                  , (df.iloc[index]['left'], df.iloc[index]['top'])
                  , (df.iloc[index]['left'] + df.iloc[index]['width'], df.iloc[index]['top'] + df.iloc[index]['height'])
                  , color
                  , 2)


def line_fast(df, image, coordinates=None, draw_lines=True):
    """
    Draw line on a image.

    Args:
        df: pandas dataframe,, contain information from page.
        image: numpy array, array of the image.
        coordinates: list, list of two tuples which contain the beginning and end of the line.
        draw_lines: bool, if true automatically draw lines on the values for <LINE> in dataframe.
    """
    if coordinates is None:
        coordinates = []
    if draw_lines:
        lines = df[df['text'] == '<LINE>']

        for Y in list(lines['top']):
            cv2.line(image, (int(0), int(Y)), (int(image.shape[0]), int(Y)), (255, 255, 0), 2)

    elif not draw_lines and type(coordinates) is tuple and len(coordinates) is 2:
        cv2.line(image, coordinates[0], coordinates[-1], (255, 255, 0), 2)


def circle_fast(image, x, y, color=(0, 255, 0)):
    """
    Draw circle on the image.
    Args:
        image: numpy array, image to draw circle on
        x: int, x coordinate of the circle
        y: int, y coordinate of the circle
        color: tuple, color of the circle
    """

    cv2.circle(image, (x, y), 3, color, 4)


def word_similarity(df, diff_list):
    """
    search the dataframe and find words which are similar to the given words

    Arguments:
        diff_list: list, contain ground truth of the words.
        df: pandas dataframe, dataframe contain words.

    Return
        df: pandas dataframe, corrected dataframe contain all words.
    """

    # Iterate over words in list and dataframe to find the similar words
    for word in diff_list:
        for index in range(len(df['text'])):

            # correct the similar words with high similarity ratio
            word2 = re.sub('[^A-Za-z0-9üöäÜÖÄß]+', '', df['text'][index])
            if difflib.SequenceMatcher(None, word, word2).ratio() > 0.89:
                if difflib.SequenceMatcher(None, word, word2).ratio() < 1:
                    df.at[index, 'text'] = word

    return df


def below_word(df, indice, regex_pattern=None, column_or_line='column', num_word=0, depth=150):
    """
    Return the below word of the given indice

    Arguments:
        df: pandas dataframe, a dataframe contain page information
        indice: integer, indice of the given value in dataframe
        regex_pattern: string, a regex pattern for finding words
        column_or_line: string, you want column or line below the indice
        num_word: integer, determine the position of below word like first word in below or second word
        depth: integer, depth of the column

    Return:
    below -- list, a list contain word bellow of the given indice
    """

    # split the below words of the specified indice
    down = df[df['top'] > df['top'][indice] + df['height'][indice] - 5]

    try:
        col = down[down['left'] > df['left'][indice] - 30]  # remove the words on the left of the indice

        # if the input variable is column then the program search the column below the word with the width of the
        # word for regex pattern
        if column_or_line is 'column':
            col1 = col[col['left'] < df['left'][indice] + df['width'][indice] + 30]
            col2 = col1[col1['top'] < df['top'][indice] + depth]
            belowww = list(col2['text'])
        # if the input variable is line the we search line below the indice for finding regex pattern
        else:
            col1 = col[col['line'] == df['line'][indice] + 1]
            belowww = list(col1['text'])

        # concat all words for searching the text
        text = ' '.join(belowww)

        if regex_pattern:  # find the input regex pattern in the text
            below = re.findall(regex_pattern, text)[num_word]

            if not below:
                below = re.findall(regex_pattern, ' '.join(list(col)))

        else:
            below = [belowww[num_word]]  # find the first word below the indice

    except:
        below = []

    return below


def clean_lines(lines):
    lin = lines.copy()

    for i in range(1, len(lines)):
        if abs(lines[i - 1][1] - lines[i][1]) < 15:
            lin.remove(lines[i - 1])

    return lin
