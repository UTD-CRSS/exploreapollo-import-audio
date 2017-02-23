import sys
import csv
import requests 
import json

#global variables - turn these into params api entry 
storyuploadurl = 'http://localhost:4060/api/stories'
momentuploadurl = 'http://localhost:4060/api/moments'	
headers = {'content-type': 'application/json', 'Authorization': 'Token token="exploreapollo"'}



def upload_moment(momentTitle, momentDescription, met_start, met_end, channel_id, story_id):
	'''
		uploads a moment with momentTitle, momentDescription, met_start (int),
		met_end(int), channel_id (int), story_id(int)
		
		Need to add error handling (can tell by catching ValueError on response.json()) 
	'''
	momentparams = {'title' : '', 'description' : '', 'met_start': 0, 'met_end' : 0, 'channel_ids' : [], 'story_ids' : []}

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
		
	storyparams = {'title': '', 'description': '', 'moment_ids': []}	
	storyparams['title'] = storyTitle
	storyparams['description'] = storyDescription
	
	response = requests.post(storyuploadurl, json=storyparams, headers=headers)
	
	data = json.loads(response.text)
	
	return data["id"]






#program begins here 
storyTitle = sys.argv[1]
storyId = upload_story(storyTitle, storyTitle) #upload story, get ID 

print storyTitle, storyId

with open('{0}.csv'.format(storyTitle), 'rb') as csvfile: 
 
	reader = csv.DictReader(csvfile)
	useTitle = ''	#to save moment title 
	usechannelID = 0	#assume all media comes from same channel in a given moment ****
	met_start_args = []
	met_end_args = []
	for moment in reader:
		
		if(moment['met_start'] == ''): #if we have a blank line, upload this moment
			print useTitle, min(met_start_args), max(met_end_args), usechannelID
			upload_moment(useTitle, useTitle, min(met_start_args), max(met_end_args), usechannelID, storyId)
			met_start_args = []
			met_end_args = []
			continue
		
		if(moment['Title'] != ''):	#if we're on the first line of a moment, save the title/channel ID 
			useTitle = moment['Title']
			usechannelID = int(moment['Transcript Files'].split('_')[2][2:]) #yikes
		
		met_start_args.append(moment['met_start'])
		met_end_args.append(moment['met_end'])
		
		
		
		