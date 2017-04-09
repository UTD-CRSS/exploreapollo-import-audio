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
		
		try:
			momentID = getMoment(moment['Title'], API_SERVER)
		except APIWarningException:
			momentID = None

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
		
_CSV_REQUIRED_FIELDS = ['Title', 'met_start', 'met_end', 'Transcript Files', 'Details']
def validate_csv(reader):
	"""
		takes a DictReader object pointing to our csv file and validates the entries.
		be sure to reset underlying file after calling this function (csvfile.seek(0))
		Returns a dictionary of rows accessed by Title to be used by later functions

	"""

	#First just check for columns existing
	precheckPass = True
	fieldsInFile = set(reader.fieldnames)
	for req in _CSV_REQUIRED_FIELDS:
		if req not in fieldsInFile:
			print("CSV: Required column %s missing in CSV file." % req)
			precheckPass = False

	if not precheckPass:
		return None

	#Next validate rows
	momentDict = {} #list of dictionary items describing each moment. Holds all fields in excel file + "canUpload"
	global storyDescription
	error = False #indicate any error in the csv
	for lineNo, row in enumerate(reader):
		
		#check blank rows 
		blankRow = True
		for i in row:
			if row[i] in (None, ""):
				row[i] = ''	#make sure we can call strip() even if entry isn't given
			else:
				blankRow = False

		#skip blank rows
		if blankRow or (len(row) == 0):
			continue


		rowValid = True
		title = row['Title'] =  row['Title'].strip()
		met_start = row['met_start'] = row['met_start'].strip()
		met_end = row['met_end'] = row['met_end'].strip()
		transcriptFile = row['Transcript Files'] = row['Transcript Files'].strip()
		audioFile = row['Audio Files'] = row['Audio Files'].strip()
		details = row['Details'] = row['Details'].strip()

		if(title == 'Description' or title == 'description'): #just the story description, save and move on
			storyDescription = details
			continue

		if(title == ''):
			rowValid = False
			print("CSV: Empty Title field found in line %d" % (lineNo+1))
		if(transcriptFile == ''):
			rowValid = False
			print("CSV: Empty Transript File field found in line %d" % (lineNo+1))
		if(audioFile == ''):
			rowValid = False
			print("CSV: Empty Audio File field found in line %d" % (lineNo+1))
		if(details == ''):
			rowValid = False
			print("CSV: Empty Details field found in line %d" % (lineNo+1))

		try:
			met_start = int(met_start)
		except ValueError:
			rowValid = False
			print("CSV: Given met_start on line %d is not a number" % (lineNo+1))
			met_start = None

		try:
 			met_end = int(met_end)
		except ValueError:
			rowValid = False
			print("CSV: Given met_start on line %d is not a number" % (lineNo+1))
			met_start = None

		if (met_start is not None) and (met_end is not None):
 			if met_start < 0:
 				print("CSV: Given met_start on line %d is less than zero" % (lineNo+1))
 				rowValid = False
 			if met_end < met_start:
 				print("CSV: met_end is less than met_start on row %d" % (lineNo+1))
 				rowValid = False

		if rowValid:
 			row['canUpload'] = True
 			momentDict[title] = row
		else:
 			error = True

 	#make sure user gave a description for story
	if storyDescription == None: 
 		print("CSV: No story description provided. Enter a row with title \"Description\" and add the story description in the \"Details\" field") 
 		error = True

	if not error:
 		return momentDict
	else:
 		return None

			 

#program begins here
storyTitle = sys.argv[1] 
storyDescription = None
storyID = -1

momentDict = None #will hold the dictionary returned by validate_csv, or None if csv error

with open('{0}.csv'.format(storyTitle), 'r') as csvfile: 
 
	reader = csv.DictReader(csvfile)
	momentDict = validate_csv(reader)
	  
if(momentDict is None):	  
	print("Please correct errors in %s.csv then rerun the program." % storyTitle)
	print("No stories or moments have been uploaded.")
	quit()
elif(checkStory(storyTitle) == True and checkMoments(momentDict) == True): #if we're clear to upload
	#upload story first, get its ID
	storyID =  upload_story(storyTitle, storyDescription,API_SERVER,API_SERVER_TOKEN)

	if(storyID == -1):	#if storyUpload fails
		print("ERROR: No existing story with name %s, but story upload failed. Exiting..." % (storyTitle))
	else: 
		for title, moment in momentDict.items():
			channelID = int(moment['Transcript Files'].split('_')[2][2:])
			upload_moment(moment['Title'], moment['Details'], moment['met_start'], moment['met_end'], channelID, storyID, API_SERVER, API_SERVER_TOKEN)
      
      
      
