import boto3
import sys
import os
import pathlib
from config import * 
from utils.APIConn import *
from utils.utils import * 
import ast

#taken from AudioUpload.py
_s3Client = None
def s3Upload(filename, bucket, destfile):
	#global _s3Client
	#if _s3Client is None:
#		_s3Client = boto3.client('s3',
#			aws_access_key_id=AWS_ACCESS_KEY,
#			aws_secret_access_key=AWS_SECRET_KEY,
#			)
#	_s3Client.upload_file(filename, bucket, destfile)
	pass

if len(sys.argv) != 3:
	print("Usage: python3 %s <local base folder> <S3 base folder>" % sys.argv[0])
	quit()
else:
	localFolder = sys.argv[1]
	s3Folder = pathlib.Path(sys.argv[2])

metricFiles = set( str(i) for i in pathlib.Path(localFolder).glob("**/*.json"))

for filepath in metricFiles:
	print(filepath)

	s3Filepath = str(s3Folder.joinpath(pathlib.Path(filepath).relative_to(localFolder)))

	print (s3Filepath)

	#upload to S3
	s3Upload(filepath, S3_BUCKET, s3Filepath)


	#upload to api server
	mission, recorder, channel, fileMetStart = filenameToParams(str(pathlib.Path(filepath).relative_to(localFolder))) #need channel, fileMetStart (ms)

	with open(filepath) as data_file:   
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