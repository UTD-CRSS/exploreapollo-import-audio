import sys
import csv

storyTitle = sys.argv[1]
#storyId = upload_story(storyTitle) --- upload story, get ID 

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
		

		
		
		
		
		
	


