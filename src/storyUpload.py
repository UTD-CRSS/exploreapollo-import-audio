import sys
import csv
import requests 
import json
from config import *
from utils.APIConn import *
		
		
def checkStory(storyTitle):
	'''
		Simply checks to be sure there is no duplicate story already in the system
		returns:
			False - story title already in the system
			True - story title not in the system
	'''

	storyID = getStory(storyTitle, API_SERVER, API_SERVER_TOKEN)

	if(storyID is not None):
		print ("ERROR: Story %s already exists (id %d)" % (storyTitle, storyID))
		return False
	else:
		return True


def checkMoments(momentDict):
	'''
		Checks to be sure the moments to upload do not
			- have the same name as a existing moment
			- have no data associated with their (met_start, met_end) interval (audio/transcript)
			- show warnings for other data not availabe (metrics/media)

			Outputs:
				goodToUpload - True if all moments do not have a name already existing, 
							   and have some audio/transcript data associated with their MET times
	'''


	goodToUpload = True 

	#check for data (audio/transcript) associated with the (met_start, met_end) interval, duplicate names 
	for title, moment in momentDict.items():
		print ("Checking moment %s..." % (title))

		audioList = getAudioSegments(moment['met_start'], moment['met_end'], API_SERVER, API_SERVER_TOKEN)
		transcriptList = getTranscriptItems(moment['met_start'], moment['met_end'], API_SERVER, API_SERVER_TOKEN)
		momentID = getMoment(moment['Title'], API_SERVER, API_SERVER_TOKEN)

		if(momentID is not None): 
			print ("ERROR: Moment %s already exists (id %d)" % (moment['Title'], momentID))
			moment['canUpload'] = False
			goodToUpload = False

		if not audioList: #if there are no audio segments for this time interval, don't allow upload 
			print ("ERROR: Moment %s has no audio data associated with its (met_start, met_end): (%d, %d)" % (moment['Title'], int(moment['met_start']), int(moment['met_end'])))
			moment['canUpload'] = False
			goodToUpload = False

		if not transcriptList: #if there are no transcript items for this time interval, don't allow upload	
			print ("ERROR: Moment %s has no transcript data associated with its (met_start, met_end): (%d, %d)" % (moment['Title'], int(moment['met_start']), int(moment['met_end'])))
			moment['canUpload'] = False
			goodToUpload = False


	return goodToUpload
		

#program begins here
storyTitle = sys.argv[1] 
storyDescription = None
storyID = -1

momentDict = {} #list of dictionary items describing each moment. Holds all fields in excel file + "canUpload"

with open('{0}.csv'.format(storyTitle), 'r') as csvfile: 
 
	reader = csv.DictReader(csvfile)
	for moment in reader:
		if(moment['Title'] == ''): #skip blank lines
			continue

		if(moment['Title'] == 'Description' or moment['Title'] == 'description'): #if its the row with the STORY description
			storyDescription = moment['Details']
		else:
			moment['canUpload'] = True	#assume we can upload it at first -- add dictionary field 
			momentDict[moment['Title']] = moment
			  

if(checkStory(storyTitle) == True and checkMoments(momentDict) == True): #if we're clear to upload
	#upload story first, get its ID
	storyID =  upload_story(storyTitle, storyDescription,API_SERVER,API_SERVER_TOKEN)

	if(storyID == -1):	#if storyUpload fails
		print("ERROR: No existing story with name %s, but story upload failed. Exiting..." % (storyTitle))
	else: 
		for title, moment in momentDict.items():
			channelID = int(moment['Transcript Files'].split('_')[2][2:])
			upload_moment(moment['Title'], moment['Details'], moment['met_start'], moment['met_end'], channelID, storyID, API_SERVER, API_SERVER_TOKEN)
      
      
      
