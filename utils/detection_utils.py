from PIL import Image
import numpy as np
import imutils
import cv2


def normalized_channel(intensity, p2, p98):
    iI = intensity
    minI = p2
    maxI = p98

    minO = 0
    maxO = 255

    iO = (iI - minI) * (((maxO - minO) / (maxI - minI)) + minO)
    return iO


def check_gray(image):
    if len(cv2.split(image)) == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return image
    else:
        return image


def max_line(lines: np.ndarray):
    if lines is not None:
        lines = lines.reshape(-1, 4)
        x1, y1, x2, y2 = lines[:, 0], lines[:, 1], lines[:, 2], lines[:, 3]
        magnitude = np.linalg.norm(np.array([x1, y1]) - np.array([x2, y2]))
        max_mag = np.argmax(magnitude)
        max_l = lines[max_mag]
        return max_l
    else:
        return None


def display_lines(image: np.ndarray, lines: np.ndarray):
    line_image = np.zeros_like(image)
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line.reshape(4)
            cv2.line(line_image, (x1, y1), (x2, y2), (0, 255, 0), 1)
            # break
    return line_image


def rotate_image(image: np.ndarray, line: np.ndarray):
    line = line.flatten()
    delta_y, delta_x = line[3] - line[1], line[2] - line[1]
    if delta_x == 0:
        return image
    slope = delta_y / delta_x
    teta_rad = np.arctan(slope)
    teta = np.rad2deg(teta_rad)
    rotated = imutils.rotate(image, teta)

    return rotated


def contrast_stretching(image: np.ndarray):
    if len(cv2.split(image)) == 3:
        blue_channel, green_channel, red_channel = cv2.split(image)
        p2, p98 = np.percentile(blue_channel, (2, 98))
        blue_channel = Image.fromarray(blue_channel).point(lambda p: normalized_channel(p, p2, p98))
        p2, p98 = np.percentile(green_channel, (2, 98))
        green_channel = Image.fromarray(green_channel).point(lambda p: normalized_channel(p, p2, p98))
        p2, p98 = np.percentile(red_channel, (2, 98))
        red_channel = Image.fromarray(red_channel).point(lambda p: normalized_channel(p, p2, p98))
        image = Image.merge('RGB', (blue_channel, green_channel, red_channel))
    elif len(cv2.split(image)) == 1:
        p2, p98 = np.percentile(image, (2, 98))
        image = Image.fromarray(image).point(lambda p: normalized_channel(p, p2, p98))
    return np.array(image)


def canny_detection(image: np.ndarray):
    image = check_gray(image)
    gauss = cv2.GaussianBlur(image, ksize=(5, 5), sigmaX=0)
    canny = cv2.Canny(gauss, 50, 150)

    return canny


def line_detection(image: np.ndarray):
    image_gray = image.copy()
    gray = cv2.cvtColor(image_gray, cv2.COLOR_BGR2GRAY)

    bw = canny_detection(gray)
    # bw = cv2.bitwise_not(bw)

    horizontal = bw.copy()

    # [horizontal lines]
    # Create structure element for extracting horizontal lines through morphology operations
    horizontalStructure = cv2.getStructuringElement(cv2.MORPH_RECT, (10, 1))

    # Apply morphology operations
    horizontal = cv2.erode(horizontal, horizontalStructure)
    horizontal = cv2.dilate(horizontal, horizontalStructure)

    horizontal = cv2.dilate(horizontal, (1, 1), iterations=3)
    horizontal = cv2.erode(horizontal, (1, 1), iterations=2)

    # HoughlinesP function to detect horizontal lines
    hor_lines = cv2.HoughLinesP(horizontal, rho=2, theta=np.pi / 180, threshold=80, minLineLength=5, maxLineGap=5)
    if hor_lines is not None:
        maximum_line = max_line(hor_lines)
        # line_image = display_lines(image_gray, np.expand_dims(maximum_line, axis=0))
        image = cv2.copyMakeBorder(image, 10, 10, 10, 10, cv2.BORDER_CONSTANT, value=[255, 255, 255])
        rotated_image = rotate_image(image, maximum_line)
        return rotated_image
    else:

        return image
