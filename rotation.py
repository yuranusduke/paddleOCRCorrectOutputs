"""
This file contains all operations about rotation of image
Completely from : https://www.freesion.com/article/46162192/

Created by Kunhong Yu
Date: 2021/02/25
"""
import cv2
import numpy as np
from math import *
from scipy.stats import mode

class ImgCorrect(object):
    """Define Image Correct class"""
    def __init__(self, img):
        self.img = img
        self.h, self.w, self.channel = self.img.shape
        if self.w <= self.h:
            self.scale = 700 / self.w
            self.w_scale = 700
            self.h_scale = self.h * self.scale
            self.img = cv2.resize(self.img, (0, 0), fx = self.scale, fy = self.scale, interpolation = cv2.INTER_NEAREST)
        else:
            self.scale = 700 / self.h
            self.h_scale = 700
            self.w_scale = self.w * self.scale
            self.img = cv2.resize(self.img, (0, 0), fx = self.scale, fy = self.scale, interpolation = cv2.INTER_NEAREST)
        self.gray = cv2.cvtColor(self.img, cv2.COLOR_BGR2GRAY)
 
 
    def img_lines(self):
        ret, binary = cv2.threshold(self.gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))  
        binary = cv2.dilate(binary, kernel) 
        edges = cv2.Canny(binary, 50, 200)
        self.lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 100, minLineLength = 100, maxLineGap = 20)
        if self.lines is None:
            print("Line segment not found")
            return None
 
        lines1 = self.lines[:, 0, :] 
        imglines = self.img.copy()
        for x1, y1, x2, y2 in lines1[:]:
            cv2.line(imglines, (x1, y1), (x2, y2), (0, 255, 0), 3)
        return imglines
 
    def search_lines(self):
        lines = self.lines[:, 0, :]  
        number_inexistence_k = 0
        sum_positive_k45 = 0
        number_positive_k45 = 0
        sum_positive_k90 = 0
        number_positive_k90 = 0
        sum_negative_k45 =0
        number_negative_k45 = 0
        sum_negative_k90 = 0
        number_negative_k90 = 0
        sum_zero_k = 0
        number_zero_k = 0
        for x in lines:
            if x[2] == x[0]:
                number_inexistence_k += 1
                continue
            print(degrees(atan((x[3] - x[1]) / (x[2] - x[0]))), "pos:", x[0], x[1], x[2], x[3], "斜率:", (x[3] - x[1]) / (x[2] - x[0]))
            if 0 < degrees(atan((x[3] - x[1]) / (x[2] - x[0]))) < 45:
                number_positive_k45 += 1
                sum_positive_k45 += degrees(atan((x[3] - x[1]) / (x[2] - x[0])))
            if 45 <= degrees(atan((x[3] - x[1]) / (x[2] - x[0]))) < 90:
                number_positive_k90 += 1
                sum_positive_k90 += degrees(atan((x[3] - x[1]) / (x[2] - x[0])))
            if -45 < degrees(atan((x[3] - x[1]) / (x[2] - x[0]))) < 0:
                number_negative_k45 += 1
                sum_negative_k45 += degrees(atan((x[3] - x[1]) / (x[2] - x[0])))
            if -90 < degrees(atan((x[3] - x[1]) / (x[2] - x[0]))) <= -45:
                number_negative_k90 += 1
                sum_negative_k90 += degrees(atan((x[3] - x[1]) / (x[2] - x[0])))
            if x[3] == x[1]:
                number_zero_k += 1
 
        max_number = max(number_inexistence_k, number_positive_k45, number_positive_k90, number_negative_k45, number_negative_k90, number_zero_k)
        if max_number == number_inexistence_k:
            return 90
        if max_number == number_positive_k45:
            return sum_positive_k45 / number_positive_k45
        if max_number == number_positive_k90:
            return sum_positive_k90 / number_positive_k90
        if max_number == number_negative_k45:
            return sum_negative_k45 / number_negative_k45
        if max_number == number_negative_k90:
            return sum_negative_k90 / number_negative_k90
        if max_number == number_zero_k:
            return 0
 
    def rotate_image(self, degree):
        #print("degree:", degree)
        if -45 <= degree <= 0:
            degree = degree # #负角度 顺时针
        if -90<= degree < -45:
            degree = 90 + degree #正角度 逆时针
        if 0 < degree <= 45:
            degree = degree #正角度 逆时针
        if 45 < degree <90:
            degree = degree - 90 #负角度 顺时针
        print("rotate degree:", degree)
        # # 获取旋转后4角的填充色
        filled_color = -1
        if filled_color == -1:
            filled_color = mode([self.img[0, 0], self.img[0, -1],
                                 self.img[-1, 0], self.img[-1, -1]]).mode[0]
        if np.array(filled_color).shape[0] == 2:
            if isinstance(filled_color, int):
                filled_color = (filled_color, filled_color, filled_color)
        else:
            filled_color = tuple([int(i) for i in filled_color])
 
        height, width = self.img.shape[:2]
        heightNew = int(width * fabs(sin(radians(degree))) + height * fabs(cos(radians(degree))))  
        widthNew = int(height * fabs(sin(radians(degree))) + width * fabs(cos(radians(degree))))
 
        matRotation = cv2.getRotationMatrix2D((width / 2, height / 2), degree, 1) #逆时针旋转 degree
 
        matRotation[0, 2] += (widthNew - width) / 2  # 因为旋转之后,坐标系原点是新图像的左上角,所以需要根据原图做转化
        matRotation[1, 2] += (heightNew - height) / 2
 
        imgRotation = cv2.warpAffine(self.img, matRotation, (widthNew, heightNew), borderValue = filled_color)

        return imgRotation