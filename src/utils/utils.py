import os.path
import json


def filenameToParams(filename):
	'''convert filename to (mission, recorder, channel, fileMetStart)
	expects a format something like A11_HR1U_CH10_00651360000.txt
	'''
	cleanFilename = os.path.splitext(os.path.split(filename)[1])[0]
	mission,recorder,rchannel,rmetstart = cleanFilename.split('_')
	
	chidx = 0
	while rchannel[chidx] not in "0123456789":
		chidx += 1
	channel = int(rchannel[chidx:])
	metstart = int(rmetstart)
	
	return (mission,recorder,channel,metstart)

def list_to_json_string(origlist):
	'''takes origlist and represents it in a string as a json list 

	example: 
		origlist = ['SPK2"', 'SPK4"', 'SPK1"', 'SPK1', 'SPK3"']

		returns '['SPK2"', 'SPK4"', 'SPK1"', 'SPK1', 'SPK3"']'
	'''

	jsonListString = '['

	for element in origlist[:-1]: 
		jsonListString += '\'{0}\','.format(element)
	jsonListString+= '\'{0}\']'.format(origlist[-1]) 


	return jsonListString


def validate_metric_json(filename):
	'''
		takes the file path of a json file representing metrics to upload
		and verifies its integrity:
		- has start_time list
		- has end_time list
		- start_time entries = end_time entries , and not empty 
		- for every list entry that is not a {speaker, interaction matrix, start_time, end_time}
		  (example: nturns, wordcount), ensure there are the same amount (or more)
		  entries in start_time and end_time lists 
	'''


	with open(filename) as data_file: 
		dataread = data_file.read().replace('\n', '') #get rid of newline in string literals in json  
		tempData = json.loads(dataread)

		initialCheckPass = True
		if 'start_time' not in tempData:
			print ("ERROR: start_time list not included.")
			initialCheckPass = False
		if 'end_time' not in tempData: 
			print("ERROR: end_time list not included.")
			initialCheckPass = False

		if not initialCheckPass:
			return False  

		metLenCheckPass = True	

		if len(tempData['start_time']) <= 0: 
			print("ERROR: start_time list cannot be empty.")
			metLenCheckPass = False
		if len(tempData['end_time']) <= 0:
			print("ERROR: end_time list cannot be empty.")
			metLenCheckPass = False

		if len(tempData['start_time']) != len(tempData['end_time']):
			print("ERROR: start_time and end_time lists must have the same number of entries.")
			metLenCheckPass = False

		if not metLenCheckPass:
			return False


		metricMatchCheck = True	


		for metricName, metricList in tempData.items():
			#don't need corresponding start_time/end for each of these entries, skip.
			if (metricName == 'start_time' or metricName == 'end_time'
				or metricName == 'speakers' or metricName == 'interaction_matrix'):
				continue

			if(len(metricList) > len(tempData['end_time'])):
				print("ERROR: not enough start_time/end_time entries for %s metric" % (metricName))
				metricMatchCheck = False

		if not metricMatchCheck:
			return False
		else:
			return True








