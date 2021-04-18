# coding=utf-8

import os
import glob
import traceback
import sys
import cv2

import scipy.spatial.distance as distance
from PIL import Image
import pytesseract

from utils.page_utils import *


class Page(object):
    def __init__(self, im, page_num=0, lang=None):
        self.healthy = True
        self.err = False
        self.page_num = page_num
        self.orig_im = im
        if len(im.shape) != 2:
            self.orig_im_gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
        else:
            self.orig_im_gray = im
        self.orig_shape = self.orig_im.shape
        self.lang = lang
        os.makedirs('temp_block', exist_ok=True)
        for file in glob.glob('temp_block' + '*/*'):
            os.remove(file)

        # special setting for each document
        self.dilate_iteration = 8
        self.kernel_size = (5,5)
        self.intersect_thresh = 0.1
        self.down_scale = False
        self.reduce_noise = True
        self.save_regions = True

    def deskew(self):
        try:
            self.orig_im = deskew_image(self.orig_im)
            self.orig_im_gray = deskew_image(self.orig_im_gray)
            return self.orig_im_gray
        except Exception as e:
            self.err = e
            self.healthy = False

    def crop(self):
        try:
            self.segmented_rects , self.segmented_images, self.segmented_images_gray = self.process_image()
            return self.segmented_rects, self.segmented_images_gray
        except Exception as e:
            for frame in traceback.extract_tb(sys.exc_info()[2]):
                fname, lineno, fn, text = frame
                print("Error in %s on line %d" % (fname, lineno))
                print(e)
            self.err = e
            self.healthy = False

    def deskew_sub_image(self):
        try:
            self.segmented_images_gray, self.theta_est = process_skewed_crop(self.segmented_images_gray)
            # for i, im in enumerate(self.segmented_images):
            #     cv2.imwrite(os.path.join('temp', str(i)+'_segment.jpg'), im)
            return self.segmented_images
        except Exception as e:
            self.err = e
            self.healthy = False

    def extract_text(self):
        self.texts = []
        temp_path = 'text_temp.png'
        for i, sub_image in enumerate(self.segmented_images):
            cv2.imwrite(temp_path, sub_image)
            text = pytesseract.image_to_string(Image.open(temp_path), lang=self.lang)
            self.texts.append(text)
        os.remove(temp_path)
        return self.texts

    def save(self, out_path):
        if not self.healthy:
            print("There was an error when cropping")
            raise Exception(self.err)
        else:
            for sub_image in self.segmented_images:
                cv2.imwrite(out_path, sub_image)

    def process_image(self):
        down_scale = self.down_scale
        reduce_noise = self.reduce_noise
        save_regions = self.save_regions
        kernel_size = self.kernel_size
        dilate_iteration = self.dilate_iteration
        intersect_thresh = self.intersect_thresh

        # Load and scale down image.
        if down_scale:
            scale, im = downscale_image(self.orig_im_gray)
        else:
            scale = 1
            im = self.orig_im_gray.copy()

        # Reduce noise.
        if reduce_noise:
            im = reduce_noise_raw(im, median_size=3)

        # Edged.
        edges = auto_canny(im)

        # Reduce noise and remove thin borders.
        debordered = reduce_noise_edges(edges)

        # Dilate until there are a few components.
        # dilation, rects, num_tries = find_components(debordered, 16)
        dilation, rects, num_tries = find_all_components(debordered, kernel_size=kernel_size, dilate_iteration=dilate_iteration)

        # Find the final crop.
        # final_rect = find_final_crop(dilation, rects)

        # Find all crop regions.
        segmented_rects = find_segmented_rect(rects, thresh=intersect_thresh)

        # Sort rects top to bottom and left to right
        segmented_rects = self.sort_rect(segmented_rects)

        # Crop the image
        cropped_segmented_images = crop_image(self.orig_im, segmented_rects, scale)
        cropped_segmented_images_gray = crop_image(self.orig_im_gray, segmented_rects, scale)

        # smooth image
        # kernel = np.ones((5, 5), np.float32) / 25
        # smooth2d = cv2.filter2D(cropped[0], -1, kernel=kernel)

        if save_regions:
            im_regions = self.orig_im.copy()
            for rect in segmented_rects:
                im_regions = cv2.rectangle(im_regions, rect[0:2], rect[2:], (0,0,255), 2)
            file_name = 'regions_' + str(self.page_num) + '.jpg'
            cv2.imwrite(os.path.join('temp', file_name), im_regions)

        return segmented_rects, cropped_segmented_images, cropped_segmented_images_gray


    def sort_rect(self, segmented_rects, threshold_value_y=40):
        rects = [[i, rect] for i, rect in enumerate(segmented_rects)]
        sorted_rects = sorted(rects, key=lambda x: x[1][1])
        num_rects = len(sorted_rects)
        # check if the next neighgour box x coordinates is greater then the current box x coordinates if not swap them.
        # repeat the swaping process to a threshold iteration and also select the threshold
        for i in range(5):
            for i in range(num_rects - 1):
                if abs(sorted_rects[i + 1][1][1] - sorted_rects[i][1][1]) < threshold_value_y and \
                        (sorted_rects[i + 1][1][0] < sorted_rects[i][1][0]):
                    tmp = sorted_rects[i]
                    sorted_rects[i] = sorted_rects[i + 1]
                    sorted_rects[i + 1] = tmp
        sorted_rects = [rect[1] for rect in sorted_rects]
        return sorted_rects
