# -*- coding: UTF-8 -*-
"""
This file contains all operations about OCR

Created by Kunhong Yu
Date: 2021/02/24
Modified: 2021/02/25
"""

from paddleocr import PaddleOCR, draw_ocr
import os
import sys
from utils import bilinear, queryresults, rotate
from PIL import Image
import fire
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

def getResult(templateList = None, 
			  return_name = None, 
			  dst_dir = './results',
			  template = 'h1', 
			  img_path = './origin_pics/bloodtestreport2.jpg', 
			  epsilon = 10,
			  weight_for_hori = 0.4,
			  side = 'middle'):
	"""
	This function is used to get Result of recognition
	Args : 
		--tempList
		--return_name
		--dis_dir
		--template
		--img_path
		--epsilon
		--weight_for_hori: horizontal line weight, default is 0.4
		--side: 'middle' or 'left' or 'right'
	return : 
		--final_results: in Python dictionary
		--final_score: final score
	"""
	assert templateList is not None
	# 0. Preprocessing
	rotate(img_path)
	# 1. Recognition
	ocr = PaddleOCR(use_angle_cls = True, lang = "ch") # need to run only once to download and load model into memory
	result = ocr.ocr(img_path, cls = True)
	res = {}

	# 2. Get bilinear coordinates
	for item in result:
		coordinates = item[0]
		upperleft = coordinates[0]
		upperright = coordinates[1]
		lowerright = coordinates[2]
		lowerleft = coordinates[-1]
		new = bilinear(upperleft, upperright, lowerright, lowerleft, side)

		res[new] = item
	#res = dict(sorted(res.items(), key = lambda x : (x[0][1], x[0][0])))

	temp_res = {}
	count = 1
	#store in the dictionary with key being detected texts value being bbox
	for line in result:
	    print('\tres : ' + line[-1][0] + ' || coor :', line[0][0])
	    if line[-1][0] in temp_res:
	    	temp_res[line[-1][0] + str(count)] = line[0][0]
	    	count += 1
	    else:
	    	temp_res[line[-1][0]] = line[0][0]

	# 3. ASIDE: show results
	result = list(res.values())
	image = Image.open(img_path).convert('RGB')
	boxes = [line[0] for line in result]
	txts = [line[1][0] for line in result]
	scores = [line[1][1] for line in result]
	final_score = sum(scores) / len(scores)
	im_show = draw_ocr(image, boxes, txts, scores, font_path = '/path/to/PaddleOCR/doc/simfang.ttf')
	im_show = Image.fromarray(im_show)
	
	saved_file = os.path.join(dst_dir, template, return_name)
	im_show.save(saved_file + '_result.jpg')

	#print('Final score is : %.2f%%.' % (final_score * 100.))

	# 3. Filter results
	# MOST IMPORTANT!
	final_results = queryresults(templateList, temp_res, epsilon, weight_for_hori)

	del res, temp_res

	return final_results, final_score

def OCR(data_dir, 
		template, 
		img_format = 'jpg', 
		recognize_all = True, 
		return_name = None, 
		epsilon = 40,
		weight_for_hori = 0.4,
		side = 'middle'):
	"""
	This function is used to recognize the pics
	Args : 
		--data_dir: data directory
		--template: which template
		--img_format: image format, default is 'jpg'
		--recognize_all: True for returning all usable results, else return the specific file
		--return_name: default is None
		--epsilon: default is 10
		--weight_for_hori: horizontal line weight, default is 0.4
		--side: 'middle' or 'left' or 'right'
	return : 
		--None
	"""
	try:
		files = os.path.join(data_dir, template)
		path = files
		files = os.listdir(files)
		files = list(filter(lambda x : x.endswith(img_format), files))
		with open(os.path.join('templates', template + '.txt'), 'r', encoding = 'utf-8') as f:
			templateList = f.read()
		templateList = templateList.split(',')

		if not recognize_all:
			assert return_name is not None
			return_file = os.path.join(path, return_name)
			assert return_name in files
			print('\tRecognizing file : %s.' % return_name)
			img_path = return_file
			final_result, score = getResult(img_path = img_path,
											templateList = templateList, 
											return_name = return_name.split('.')[0], 
											dst_dir = './results', 
											template = template, 
											epsilon = epsilon,
											weight_for_hori = weight_for_hori,
											side = 'middle')
			string = str(final_result) + ' || ' + '%.2f%%' % (score * 100.) + '\n'
			with open(os.path.join('./results', template, return_name.split('.')[0] + '_result.txt'), 'a+') as f:
				f.write(string)

			print('\n' + string)

		else:
			string = ''
			for i, file in enumerate(files):
				print('\tRecognizing %d / %d file : %.s.' % (i + 1, len(files), file))
				img_path = os.path.join(path, file)
				final_result, score = getResult(img_path = img_path, 
												return_name = file.split('.')[0], 
												templateList = templateList,
												dst_dir = './results', 
												template = template, 
												epsilon = epsilon,
												weight_for_hori = weight_for_hori,
												side = 'middle')
				string += str(final_result) + ' || ' + '%.2f%%' % (score * 100.) + '\n'
				print('\n' + string)
			with open(os.path.join('./results', template, return_name.split('.')[0] + '_result.txt'), 'a+') as f:
				f.write(string)

	except:
		raise Exception('Error happend! EXIT!')

	else:
		print('\nRecognition done!')
		print("You can query results in './results/ %s'.\n" % (template))


"""
USAGE:
Before running the recognition code, this will rotate image back if the rotated degree is between [-pi, pi]
Args : 
	--data_dir: data directory, default is 'origin_pics'
	--template: which template, you can specify the some directory
	--img_format: image format, default is 'jpg'
	--recognize_all: True for returning all usable results, else return the specific file
	--return_name: default is None, but if you set recognize_all equals False, you must set return_name to be a specific value
	--epsilon: default is 40, if you set epsilon too high or too low, the results may be not promising, the LARGET the BETTER
	--weight_for_hori: horizontal line weight, default is 0.4
	--side: 'middle' or 'left' or 'right', to tell where are texts and 结果 aligned
In the project file
origin_pics contains all templates images
results must contain all template results
templates contain TXT files for each template
every files' templates' names must be the same
"""
"""
To run the code, you can run the following command in shell:
python process.py OCR --data_dir='origin_pics' --template='h5' \
--img_format='jpg' --recognize_all=True --return_name='bloodtestreport2.jpg' --epsilon=40 --weight_for_hori=0.4 --side='middle'
"""
if __name__ == '__main__':
	fire.Fire()
#yaoyansheOCR('origin_pics', 'h2', img_format = 'jpg', recognize_all = True, return_name = 'bloodtestreport2.jpg', epsilon = 40)

"""
Shortages:
If paddle cannot recognize '结果' correctly, the results can be confused.
My algorithm still has some limitations, e.g., I can not use OpenCv to rotate image if image is mirrored, because
OpenCV uses Hough transformation to detect lines.
For different styles of receipts, we still have to set templates separately.
"""