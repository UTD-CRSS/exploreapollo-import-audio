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
storyId = upload_story(storyTitle, "placeholder") #upload story, get ID 

print storyId

with open('{0}.csv'.format(storyTitle), 'rb') as csvfile: 
 
	lastTitle = '' #holds the last title read
	i = 2
	reader = csv.DictReader(csvfile)
	for moment in reader:
		useTitle = ''
	
		if(moment['met_start'] == ''): #if we have a blank line
			continue
 
		if(moment['Title'] != ''):
			lastTitle = moment['Title']
			useTitle = moment['Title']
			i = 2
		else:
			useTitle = '{0}_{1}'.format(lastTitle, i)
			i = i + 1
		
		channelID = int(moment['Transcript Files'].split('_')[2][2:]) #yikes
		print useTitle, moment['met_start'], moment['met_end'], channelID
		upload_moment(useTitle, "placeholders description", moment['met_start'], moment['met_end'], channelID, storyId)

		

	
	


