import sys
import csv
import requests 
import json

#global variables
storyuploadurl = 'http://localhost:4060/api/stories'
momentuploadurl = 'http://localhost:4060/api/moments'	
headers = {'content-type': 'application/json', 'Authorization': 'Token token="exploreapollo"'}

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

		print useTitle, moment['met_start'], moment['met_end'], moment['Transcript Files']
		

		

	
	


