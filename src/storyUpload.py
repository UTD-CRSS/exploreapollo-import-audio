import sys
import csv
import requests 
import json
from config import *
from utils.APIConn import *


#program begins here 
#storyTitle = sys.argv[1]
#storyDescription = "placeholder"
#storyId = upload_story(storyTitle, storyDescription, API_SERVER, API_SERVER_TOKEN) #upload story, get ID 


#with open('{0}.csv'.format(storyTitle), 'r') as csvfile: 
 
#	reader = csv.DictReader(csvfile)
#	for moment in reader:
#		
#
#		channelID = int(moment['Transcript Files'].split('_')[2][2:])
#		print useTitle, moment['met_start'], moment['met_end'], channelID
#		upload_moment(moment['Title'], moment['Details'], moment['met_start'], moment['met_end'], channelID, storyId, API_SERVER, API_SERVER_TOKEN)
		


#program begins here
storyTitle = sys.argv[1] 
storyDescription = None
storyID = -1

momentDict = {} #list of dictionary items describing each moment. Holds all fields in excel file + "canUpload"

with open('{0}.csv'.format(storyTitle), 'r') as csvfile: 
 
	reader = csv.DictReader(csvfile)
	for moment in reader:
		if(moment['Title'] = ''): #skip blank lines
			continue

		if(moment['Title'] == 'Description' or moment['Title'] == 'description'): #if its the row with the STORY description
			storyDescription = moment['Details']
		else:
			moment['canUpload'] = True	#assume we can upload it at first -- add dictionary field 
			momentDict[moment['Title']] = moment 
			  



if(checkStory(storyTitle) == True and checkMoments(momentDict) == True): #if we're clear to upload





		

		

	
	


