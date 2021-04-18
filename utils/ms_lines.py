import numpy as np
from cv2 import cv2
import pandas as pd
from sklearn.cluster import MeanShift


def _find_lines(dataframe: pd.DataFrame, **kwargs):
    if 'bandwidth' in kwargs.keys():
        clustering = MeanShift(bandwidth=kwargs['bandwidth'])
    else:
        clustering = MeanShift(bandwidth=20)

    y_mean = dataframe['top']  # + dataframe['height']) // 2
    y_mean = np.sort(y_mean)
    y_mean = np.expand_dims(y_mean, axis=1)

    clustering.fit(y_mean)
    labels = clustering.labels_
    labels_ = np.zeros(labels.shape, dtype=np.uint8)
    _, idx = np.unique(labels, return_index=True)
    uniques = labels[np.sort(idx)]
    for i, label in enumerate(uniques):
        labels_[labels == label] = i+1

    return labels_, y_mean


def draw_lines(image: np.ndarray, dataframe: pd.DataFrame):
    lines, y_mean = _find_lines(dataframe)
    unique_lines = np.unique(lines)
    dataframe['lines'] = lines
    img = image.copy()
    for line in unique_lines:
        mean = int(y_mean[lines == line].mean())
        # cv2.circle(img, (20, mean), 5, (128, 128, 0), -1)
        cv2.putText(img, str(line + 1), (30, mean), cv2.FONT_HERSHEY_SIMPLEX, 1, (115, 115, 155))
    return img


def find_lines(dataframe: pd.DataFrame, **kwargs):
    lines, y_mean = _find_lines(dataframe, **kwargs)
    dataframe['line'] = lines

    return dataframe
