# -*- coding: UTF-8 -*-
"""
This file contains all operations about OCR utilities

Created by Kunhong Yu
Date: 2021/02/24
Modified: 2021/02/25
"""
from copy import deepcopy
import os
import sys
import math
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import difflib
import cv2
import numpy as np
from rotation import ImgCorrect

def get_equal_rate(str1, str2):
	"""This function is used to get similarity of two strings
	Args : 
		--str1: string 1
		--str2: string 2
	return : 
		--similarity
	"""
	return difflib.SequenceMatcher(None, str1, str2).quick_ratio()

def rotate(img_path):
	"""This function is used to rotate original image back
	Args : 
		--img_path
	return :
		--no return, we just overwrite original img
	"""
	img = cv2.imread(img_path)
	imgcorrect = ImgCorrect(img)
	lines_img = imgcorrect.img_lines()
	if lines_img is None:
	    rotated = imgcorrect.rotate_image(0)
	else:
	    degree = imgcorrect.search_lines()
	    rotated = imgcorrect.rotate_image(degree)
	cv2.imwrite(img_path, rotated)

def bilinear(upperleft, upperright, lowerright, lowerleft, side = 'middle'):
	"""
	This function is used to do bilinear projection of coordinates
	Args : 
		--upperleft
		--upperleft
		--upperright
		--lowerright
		--lowerleft
		--side: 'middle' or 'left' or 'right'
	return :
	 	--blineared coordinate
	"""
	x1, y1, x2, y2, x3, y3, x4, y4 = upperleft[0], upperleft[1], upperright[0], upperright[1], lowerright[0], lowerright[1], lowerleft[0], lowerleft[1]
	y14 = (y1 + y4) / 2.
	y23 = (y2 + y3) / 2.
	y = (y14 + y23) / 2.
	x12 = (x1 + x2) / 2.
	x43 = (x4 + x3) / 2.
	x = (x12 + x43) / 2.

	if side == 'middle':
		return (x, y)
	elif side == 'left':
		return ((x1 + x4) / 2., y4)
	elif side == 'right':
		return ((x2 + x3) / 2., y3)# get middle right coordinate
	else:
		raise Exception('No other sides!')

def queryresults(templateList, res, epsilon, weight_for_hori):
	"""
	This function is used to query results, this is the most important function
	Args : 
		--templateList: ['', '']
		--res: Python dictionary {detected chars : bilinear coordinates}
		--epsilon: redunance
		--weight_for_hori: horizontal line weight, default is 0.4
	return : 
		--all_results: in Python dictionary
	"""
	# get Results column#
	coor_result = None
	all_results = {}
	temp_all_results = {}
	coor_results = []
	all_items = res.items()
	temp = deepcopy(res)
	for k, v in all_items:
		if k.count('结果'):
			temp.pop(k)
			coor_result = v
			coor_results.append(coor_result)#multiple same results, typically 2 results

	res = deepcopy(temp)
	del temp

	if coor_result is None:
		raise Exception('No 结果 detected!')

	x, y = coor_results[0][0], coor_results[0][1]
	res_range1 = (x - epsilon, x + epsilon)#vertical 1
	if len(coor_results) > 1:
		x, y = coor_results[1][0], coor_results[1][1]
		res_range2 = (x - epsilon, x + epsilon)#vertical 2

	else:
		res_range2 = res_range1

	for item in templateList:#for each item, we iterate through the whole dictionary to find corresponding value
		coor_result = None
		for k, v in res.items():
			if get_equal_rate(k, item) > 0.8:#string match
				res.pop(k)
				coor_result = v
				break

		if coor_result is None:
			all_results[item] = 'NOT DETECTED'

		else:
			x, y = coor_result[0], coor_result[1]
			#x_range = (x - epsilon, x + epsilon)
			y_range = (y - epsilon, y + epsilon)#横坐标

			for k, v in res.items():
				#First, filter all results in the range of [x - epsilon, x + epsilon] and [y - epsilon, y + epsilon]
				if ((y_range[0] <= v[1] <= y_range[1]) and (res_range1[0] <= v[0] <= res_range1[1])) \
					or ((y_range[0] <= v[1] <= y_range[1]) and (res_range2[0] <= v[0] <= res_range2[1])):
					#Then, we filter closer results in the same range, if we get two columns, v[0] - x makes sure
					#we can find closer one, if we get multiple rows abs(v[1] - y) makes sure we can find nearest one
					now_residual = (v[0] - x) * weight_for_hori + abs(v[1] - y) * (1 - weight_for_hori)#weighted to say vertical line is more important
					
					if (v[0] - x) >= 0:
						if item not in temp_all_results:
							temp_all_results[item] = now_residual
							all_results[item] = k
						else:
							residual = temp_all_results[item]
							if residual > now_residual:
								temp_all_results[item] = now_residual#compare residual, if old one is larger than the new one, then this key must be better
								all_results[item] = k

							# res.pop(k)
							# break

	return all_results