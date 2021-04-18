import os
import cv2
import numpy as np
from scipy.ndimage.filters import rank_filter


def auto_canny(image, sigma=0.33):
    v = np.median(image)
    lower = int(max(0, (1.0 - sigma) * v))
    upper = int(min(255, (1.0 + sigma) * v))
    edged = cv2.Canny(image, lower, upper, True)
    return edged


def dilate(image, kernel, iterations):
    dilated_image = cv2.dilate(image, kernel, iterations=iterations)
    return dilated_image


def downscale_image(im, max_dim=2048):
    """Shrink im until its longest dimension is <= max_dim.
    Returns new_image, scale (where scale <= 1)."""
    a, b = im.shape[:2]
    if max(a, b) <= max_dim:
        return 1.0, im

    scale = 1.0 * max_dim / max(a, b)
    new_im = cv2.resize(im, (int(b * scale), int(a * scale)), cv2.INTER_AREA)
    return scale, new_im


def find_components(im, max_components=16):
    """Dilate the image until there are just a few connected components.
    Returns contours for these components."""
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (10, 10))
    dilation = dilate(im, kernel, 6)

    count = 21
    n = 0
    sigma = 0.000

    while count > max_components:
        n += 1
        sigma += 0.005
        result = cv2.findContours(dilation, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        if len(result) == 3:
            _, contours, hierarchy = result
        elif len(result) == 2:
            contours, hierarchy = result
        possible = find_likely_rectangles(contours, sigma)
        count = len(possible)

    return (dilation, possible, n)


def find_all_components(im, kernel_size=(7,5), dilate_iteration=6):
    """Dilate the image until there are just a few connected components.
    Returns contours for these components."""
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, kernel_size)
    dilation = dilate(im, kernel, dilate_iteration)
    n = 1
    sigma = 0.01
    result = cv2.findContours(dilation, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    if len(result) == 3:
        _, contours, hierarchy = result
    elif len(result) == 2:
        contours, hierarchy = result
    possible = find_likely_rectangles(contours, sigma, n_contour=200)

    # for c in contours:
    #     rect = cv2.minAreaRect(c)
    #     box = cv2.boxPoints(rect)
    #     box = np.int0(box)
    #     center = rect[0]
    #     rotation = rect[2]
    #     width = rect[1][0]
    #     height = rect[1][1]
    #     cv2.drawContours(im, [box], 0, (0, 0, 255), 2)
    # cv2.imwrite(os.path.join('temp', 'box.jpg'), im)

    return (dilation, possible, n)


def find_likely_rectangles(contours, sigma, n_contour=10):
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:n_contour]
    possible = []
    for c in contours:
        # approximate the contour
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, sigma * peri, True)
        box = make_box(approx)
        possible.append(box)

    return possible


def make_box(poly):
    x = []
    y = []
    for p in poly:
        for point in p:
            x.append(point[0])
            y.append(point[1])
    xmax = max(x)
    ymax = max(y)
    xmin = min(x)
    ymin = min(y)
    return (xmin, ymin, xmax, ymax)


def rect_union(crop1, crop2):
    """Union two (x1, y1, x2, y2) rects."""
    x11, y11, x21, y21 = crop1
    x12, y12, x22, y22 = crop2
    return min(x11, x12), min(y11, y12), max(x21, x22), max(y21, y22)


def rect_area(crop):
    x1, y1, x2, y2 = crop
    return max(0, x2 - x1) * max(0, y2 - y1)


def crop_image(im, rects, scale):
    cropped_sub_images = []
    for rect in rects:
        xmin, ymin, xmax, ymax = rect
        crop = [xmin, ymin, xmax, ymax]
        xmin, ymin, xmax, ymax = [int(x / scale) for x in crop]
        cropped = im[ymin:ymax, xmin:xmax]
        cropped_sub_images.append(cropped)
    return cropped_sub_images


def reduce_noise_raw(im, median_size=5):
    bilat = cv2.bilateralFilter(im, 9, 75, 75)
    blur = cv2.medianBlur(bilat, median_size)
    return blur


def reduce_noise_edges(im):
    structuring_element = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
    opening = cv2.morphologyEx(im, cv2.MORPH_OPEN, structuring_element)
    maxed_rows = rank_filter(opening, -4, size=(1, 20))
    maxed_cols = rank_filter(opening, -4, size=(2, 20))
    debordered = np.minimum(np.minimum(opening, maxed_rows), maxed_cols)
    return debordered


def rects_are_vertical(rect1, rect2):
    xmin1, ymin1, xmax1, ymax1 = rect1
    xmin2, ymin2, xmax2, ymax2 = rect2

    midpoint1 = (xmin1 + xmax1) / 2
    midpoint2 = (xmin2 + xmax2) / 2
    dist = abs(midpoint1 - midpoint2)

    rectarea1 = rect_area(rect1)
    rectarea2 = rect_area(rect2)
    if rectarea1 > rectarea2:
        thres = (xmax1 - xmin1) * 0.1
    else:
        thres = (xmax2 - xmin2) * 0.1
    if thres > dist:
        align = True
    else:
        align = False
    return align


def find_final_crop(im, rects):
    current = None
    for rect in rects:
        if current is None:
            current = rect
            continue

        aligned = rects_are_vertical(current, rect)

        if not aligned:
            continue

        current = rect_union(current, rect)
    return current


def find_segmented_rect(rects, thresh=0.2):
    if len(rects) < 2:
        return rects
    segmented_rects = []
    while True:
        if len(rects) == 1:
            segmented_rects.append(rects[0])
            break
        areas = [rect_area(rect) for rect in rects]
        order = sorted(range(len(areas)), key=lambda k: areas[k], reverse=True)
        rects = [rects[ind] for ind in order]
        bigger_rect = rects[0]
        other_rects = rects[1:]
        ious = [sudi_iou(bigger_rect, rect) for rect in other_rects]
        inds = [j + 1 for j, iou in enumerate(ious) if iou > thresh]
        if len(inds) == 0:
            segmented_rects.append(bigger_rect)
            rects = rects[1:]
        else:
            candidate_inds = [0] + inds
            candidate_rects = [rects[j] for j in candidate_inds]
            new_bigger_rect = join_rects(candidate_rects)
            order = [j for j in range(1, len(rects)) if j not in candidate_inds]
            rects = [new_bigger_rect] + [rects[j] for j in order]

    return segmented_rects


def join_rects(rects):
    x1 = min([rect[0] for rect in rects])
    y1 = min([rect[1] for rect in rects])
    x2 = max([rect[2] for rect in rects])
    y2 = max([rect[3] for rect in rects])
    return (x1, y1, x2, y2)


def sudi_iou(rect1, rect2):
    x1 = max(rect1[0], rect2[0])
    y1 = max(rect1[1], rect2[1])
    x2 = min(rect1[2], rect2[2])
    y2 = min(rect1[3], rect2[3])
    w = max(0.0, x2 - x1 + 1)
    h = max(0.0, y2 - y1 + 1)
    inter = w * h
    iou = inter / (rect_area(rect2) + 1e-6)
    return iou


def rad_to_deg(theta):
    return theta * 180 / np.pi


def rotate(image, theta):
    (h, w) = image.shape[:2]
    center = (w / 2, h / 2)
    M = cv2.getRotationMatrix2D(center, theta, 1)
    rotated = cv2.warpAffine(image, M, (int(w), int(h)), cv2.INTER_LINEAR,
                             borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255))
    return rotated


def estimate_skew(image):
    edges = auto_canny(image)
    lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)
    new = edges.copy()

    if lines is None:
        return 90

    thetas = []
    for line in lines:
        for rho, theta in line:
            a = np.cos(theta)
            b = np.sin(theta)
            x0 = a * rho
            y0 = b * rho
            x1 = int(x0 + 1000 * (-b))
            y1 = int(y0 + 1000 * (a))
            x2 = int(x0 - 1000 * (-b))
            y2 = int(y0 - 1000 * (a))
            if theta > np.pi / 3 and theta < np.pi * 2 / 3:
                thetas.append(theta)
                new = cv2.line(new, (x1, y1), (x2, y2), (255, 255, 255), 1)
    cv2.imwrite(os.path.join('temp', 'edge.jpg'), new)

    theta_mean = np.mean(thetas)
    theta = rad_to_deg(theta_mean) if len(thetas) > 0 else 0

    return theta


def compute_skew(theta):
    # We assume a perfectly aligned page has lines at theta = 90 deg
    diff = 90 - theta

    # We want to reverse the difference.
    return -diff


def process_skewed_crop(images):
    rotation_angles = []
    rotated_images = []
    for image in images:
        theta = estimate_skew(image)
        theta = compute_skew(theta)
        ret, thresh = cv2.threshold(image.copy(), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        rotated_image = rotate(thresh, theta)

        cv2.imwrite(os.path.join('temp', 'edge.jpg'), rotated_image)

        rotation_angles.append(theta)
        rotated_images.append(rotated_image)
    return (rotated_images, rotation_angles)



def deskew_image(image, max_skew=10):
    if len(image.shape) == 2:
        height, width = image.shape
        # Create an inverted B&W copy using Otsu (automatic) thresholding
        im_bw = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    elif len(image.shape) == 3:
        height, width, _ = image.shape
        image_gs = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        im_bw = cv2.threshold(image_gs, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    else:
        return image

    # Detect lines in this image. Parameters here mostly arrived at by trial and error.
    lines = cv2.HoughLinesP(
        im_bw, 1, np.pi / 180, 200, minLineLength=width / 12, maxLineGap=width / 150
    )

    # Collect the angles of these lines (in radians)
    angles = []
    for line in lines:
        x1, y1, x2, y2 = line[0]
        angles.append(np.arctan2(y2 - y1, x2 - x1))

    # If the majority of our lines are vertical, this is probably a landscape image
    landscape = np.sum([abs(angle) > np.pi / 4 for angle in angles]) > len(angles) / 2

    # Filter the angles to remove outliers based on max_skew
    if landscape:
        angles = [
            angle
            for angle in angles
            if np.deg2rad(90 - max_skew) < abs(angle) < np.deg2rad(90 + max_skew)
        ]
    else:
        angles = [angle for angle in angles if abs(angle) < np.deg2rad(max_skew)]

    if len(angles) < 5:
        # Insufficient data to deskew
        return image

    # Average the angles to a degree offset
    angle_deg = np.rad2deg(np.median(angles))

    # If this is landscape image, rotate the entire canvas appropriately
    if landscape:
        if angle_deg < 0:
            im = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
            angle_deg += 90
        else:
            im = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
            angle_deg -= 90
        M = cv2.getRotationMatrix2D((width / 2, height / 2), angle_deg, 1)
        aligned_image = cv2.warpAffine(im, M, (height, width), borderMode=cv2.BORDER_REPLICATE)
    else:
        # Rotate the image by the residual offset
        M = cv2.getRotationMatrix2D((width / 2, height / 2), angle_deg, 1)
        aligned_image = cv2.warpAffine(image, M, (width, height), borderMode=cv2.BORDER_REPLICATE)

    return aligned_image
