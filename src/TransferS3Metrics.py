import boto3
import os
from config import *
from utils.utils import *
from utils.APIConn import *
import json
import ast




if len(sys.argv) == 1:
		target_channel = met_min = met_max = None
elif len(sys.argv) == 4:
	target_channel   = int(sys.argv[1])
	met_min = int(sys.argv[2])
	met_max   = int(sys.argv[3])
else:
	print("Usage: %s [channel met_min met_max]" % sys.argv[0])
	quit()


s3 = boto3.session.Session(aws_access_key_id=AWS_ACCESS_KEY,
		aws_secret_access_key=AWS_SECRET_KEY).resource('s3')
bucket = s3.Bucket(S3_BUCKET)

objcollection = {} #objcollection['fname_no_ext'] = jsonobj
	
numobjs = 0
for obj in bucket.objects.all(): # get all files in all folders? (graphical data, audio, static imgs?)
	name,ext = os.path.splitext(obj.key)
	if(ext == '.json'):
		objcollection[name] = obj
		numobjs+=1

itemno = 1
for name, jsonobj in objcollection.items():
	
	mission, recorder, channel, fileMetStart = filenameToParams(jsonobj.key) #need channel, fileMetStart (ms)

	if met_max is not None and (fileMetStart > met_max or fileMetStart < met_min or channel != target_channel):
		continue

	print("%s (%d/%d)" % (name,itemno,numobjs))
	itemno+=1

	bucket.download_file(jsonobj.key,'tmp.json')
	if os.path.getsize('tmp.json') <= 0: #skip empty json files.. 
		continue

	

	with open('tmp.json') as data_file:   
		#print (data_file.read())
		tempData = ast.literal_eval(data_file.read().replace('array(', '"').replace(')', '"').replace('\n', '')) #ew
	
	print(tempData)	
	

	#upload wordcounts
	for i, wordCount in enumerate(tempData['word_count']): 
		Type = "WordCount"
		met_start = int(fileMetStart) + int(float(tempData['start_time'][i]) * 1000) 
		met_end = int(fileMetStart) + int(float(tempData['end_time'][i]) * 1000)
		channel_id = channel 
		data = {
			'count'	:	wordCount
		}	

		upload_metric(Type, met_start, met_end, channel_id, data, API_SERVER , API_SERVER_TOKEN)

	#upload nturns	
	for i, nturns in enumerate(tempData['nturns']):
		Type = "Nturns"
		met_start = int(fileMetStart) + int(float(tempData['start_time'][i]) * 1000) 
		met_end = int(fileMetStart) + int(float(tempData['end_time'][i]) * 1000)
		channel_id = channel 
		data = {
			'count'	:	nturns
		}	

		upload_metric(Type, met_start, met_end, channel_id, data, API_SERVER , API_SERVER_TOKEN)

	#upload conversation counts
	for i, conversationCount in enumerate(tempData['conversation_count']):
		Type = "ConversationCount"
		met_start = int(fileMetStart) + int(float(tempData['start_time'][i]) * 1000) 
		met_end = int(fileMetStart) + int(float(tempData['end_time'][i]) * 1000)
		channel_id = channel 
		data = {
			'count'	:	conversationCount
		}	

		upload_metric(Type, met_start, met_end, channel_id, data, API_SERVER , API_SERVER_TOKEN)

	#upload speakers 
	Type = "Speakers"
	met_start = int(fileMetStart)
	met_end = int(fileMetStart) + int(max(list(map(float, tempData['end_time']))) * 1000)
	channel_id = channel
	data = {
		'names'	:	list_to_json_string(tempData['speakers'])
	}

	upload_metric(Type, met_start, met_end, channel_id, data, API_SERVER , API_SERVER_TOKEN)


	Type = "InteractionMatrix"
	met_start = int(fileMetStart)
	met_end = int(fileMetStart) + int(max(list(map(float, tempData['end_time']))) * 1000)
	channel_id = channel
	data = {
		'matrix'	:	tempData['interaction_matrix']
	}

	upload_metric(Type, met_start, met_end, channel_id, data, API_SERVER , API_SERVER_TOKEN)

	
	



	
