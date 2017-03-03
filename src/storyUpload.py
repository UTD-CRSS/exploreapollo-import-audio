import sys
import csv
import requests 
import json
from config import *

#global variables - headers
headers = {'content-type': 'application/json', 'Authorization': "Token token=%s" % API_SERVER_TOKEN}



def upload_moment(momentTitle, momentDescription, met_start, met_end, channel_id, story_id):
	'''
		uploads a moment with momentTitle, momentDescription, met_start (int),
		met_end(int), channel_id (int), story_id(int) 
	'''
	
	momentuploadurl = "%s/api/moments" % API_SERVER
	
	
	momentparams['title'] = momentTitle
	momentparams['description'] = momentDescription
	momentparams['met_start'] = met_start
	momentparams['met_end'] = met_end
	momentparams['channel_ids'].append(channel_id)
	momentparams['story_ids'].append(story_id)
	
	response = requests.post(momentuploadurl, json=momentparams, headers=headers)
	
	

def upload_story(storyTitle, storyDescription):
	'''
		uploads a story with storyTitle, storyDescription,
		and empty moment_ids. Returns story_id so moments uploaded
		later in script can use this to be associated with the story.
	'''
	
	storyuploadurl = "%s/api/storiers" % API_SERVER
			
	storyparams['title'] = storyTitle
	storyparams['description'] = storyDescription
	storyparams['moment_ids'] = []
	
	response = requests.post(storyuploadurl, json=storyparams, headers=headers)
	
	data = json.loads(response.text)
	
	return data["id"]






#program begins here 
storyTitle = sys.argv[1]
storyDescription = "placeholder"
storyId = upload_story(storyTitle, storyDescription) #upload story, get ID 

print (storyId, storyTitle, storyDescription)

with open('{0}.csv'.format(storyTitle), 'rb') as csvfile: 
 
	reader = csv.DictReader(csvfile)
	for moment in reader:
		channelID = int(moment['Transcript Files'].split('_')[2][2:])
		if(check_params(moment['met_start'], moment['met_end'], channelID)){ #if we are good to upload 
			print useTitle, moment['met_start'], moment['met_end'], channelID
			upload_moment(moment['Title'], moment['Details'], moment['met_start'], moment['met_end'], channelID, storyId)
		}
		else{
			print "Upload of %s moment failed."
		}
		
		

		

	
	


