import sys
import boto3
import pathlib
import requests
import csv
from config import *
import utils.APIConn as api
from utils.utils import *
import utils.FlickrAPI as flickr


_s3Client = None
def s3Upload(f,bucket,destfile):
	'''Put a file-like object in s3.'''
	global _s3Client
	if _s3Client is None:
		_s3Client = boto3.client('s3',
			aws_access_key_id=AWS_ACCESS_KEY,
			aws_secret_access_key=AWS_SECRET_KEY,
		)
	_s3Client.upload_fileobj(f,bucket,destfile)



_CSV_REQUIRED_FIELDS = ['media_title','attachable_type',
	'attachable_title','met_start','met_end']


def getAttachablesFromFile(filename):
	'''parse the csv to obtain all the needed values.
	Enforces strict validation, a single error will
	stop all the file processing.'''
	res = {}
	with open(filename,'r') as f:
		reader = csv.DictReader(f)
		
		#check that necessary fields are contained
		precheckPass = True
		fieldsInFile = set(reader.fieldnames)
		for req in _CSV_REQUIRED_FIELDS:
			if req not in fieldsInFile:
				print("CSV: Required column %s missing in CSV file." % req)
				precheckPass = False
				
		if not precheckPass:
			return None
		
		error = False
		
		for lineNo, row in enumerate(reader):
			if len(row) == 0:
				continue
			
			for i in row:
				if row[i] is None:
					row[i] = ''
			
			#validate row
			rowValid = True
			mediaTitle = row['media_title'].strip()
			attachableType = row['attachable_type'].strip()
			attachableTitle = row['attachable_title'].strip()
			
			if mediaTitle == '':
				rowValid = False
				print("CSV: Empty media_title field found in line %d" % (lineNo+1))
			if attachableType != 'Channel' and attachableType != 'Moment':
				rowValid = False
				print("CSV: attachable_type must be either Channel or Moment, line %d" % (lineNo+1))
			if attachableTitle == '':
				rowValid = False
				print("CSV: Empty attachable_title field found in line %d" % (lineNo+1))
			
			if row['met_start'].strip() == '':
				metStart = None
			else:
				try:
					metStart = int(row['met_start'])
				except ValueError:
					rowValid = False
					print("CSV: Given met_start on line %d is not a number" % (lineNo+1))
			if row['met_end'].strip() == '':
				metEnd = None
			else:
				try:
					metEnd = int(row['met_end'])
				except ValueError:
					rowValid = False
					print("CSV: Given met_end on line %d is not a number" % (lineNo+1))
			
			if metEnd is not None and metStart is not None:
				if metStart < 0:
					rowValid = False
					print("CSV: met_start on line %d is less than zero" % (lineNo+1))
				if metEnd < metStart:
					rowValid = False
					print("CSV: met_end is less than met_start on row %d" % (lineNo+1))
			elif metEnd is not None or metStart is not None:
				rowValid = False
				print("CSV: Either only met_start or met_end provided, must provide both or none, line %d" % (lineNo+1))
			
			if not rowValid:
				error = True
				continue
			
			#add row to results.
			if mediaTitle not in res:
				res[mediaTitle] = []
			
			res[mediaTitle].append((attachableType,
				attachableTitle,metStart,metEnd))
	
	if not error:
		return res
	else:
		return None



if __name__ == "__main__":
	argerror = False
	if len(sys.argv) > 1 and \
			(sys.argv[1] == 'flickr' or sys.argv[1] == 'local'):
		if len(sys.argv) == 5:
			albumID = sys.argv[2]
			s3Folder = pathlib.Path(sys.argv[3])
			mission = sys.argv[4]
			attachfile = None
		elif len(sys.argv) == 6:
			albumID = sys.argv[2]
			s3Folder = pathlib.Path(sys.argv[3])
			mission = sys.argv[4]
			attachfile = sys.argv[5]
		else:
			argerror = True
	elif len(sys.argv) == 2:
		albumID = None
		s3Folder = None
		mission = None
		attachfile = sys.argv[1]
	else:
		argerror = True
	
	if argerror:
		print(("Usage, local folder: %s local <local folder> "
			"<S3 folder> <Mission name> [media attachable csv]") \
			% sys.srgv[0]
		print(("Usage, flickr album: %s flickr <Flickr album id> "
			"<S3 folder> <Mission name> [media attachable csv]") \
			% sys.argv[0])
		print('Ex: %s 0001 photo "Apollo 11"')
		print(("Usage, media attachments only: %s "
			"<media attachable csv>") % sys.argv[0])
		quit()
	
	if attachfile is not None:
		attachables = getAttachablesFromFile(attachfile)
		if attachables is None:
			print("Please correct errors in %s then rerun the program." % attachfile)
			print("No images or media associations have been uploaded.")
			quit()
	else:
		attachables = {}
	
	if albumID is not None:
		albumList = flickr.getAlbumPhotoList(albumID,FLICKR_ACCESS_KEY)
	else:
		albumList = []
	
	#ensure all referenced images in CSV file exist in album or in database
	imgsExistCheck = True
	imgNames = set([name for name,url,desc in albumList])
	existingMediaIDs = {}
	
	for attachment in attachables:
		try:
			iid = api.getMedia(attachment,API_SERVER,API_SERVER_TOKEN)
			existingMediaIDs[attachment] = iid
		except api.APIWarningException:
			if attachment not in imgNames:
				print(("Error: Image %s not in databse "
					"or new album") % attachment)
				imgsExistCheck = False
	
	if not imgsExistCheck:
		print(("CSV file contains references to images not found in "
			"the database or new album."))
		print("Please remove the references and rerun the program.")
		quit()
	
	#ensure all referenced channels and moments in CSV exist
	attachablesExist = True
	for mediaItem in attachables:
		for attachType, attachName, metSt, metEnd in attachables[mediaItem]:
			if attachType == 'Moment':
				try:
					api.getMoment(attachName,API_SERVER)
				except api.APIWarningException:
					print(("Error: moment %s referenced in CSV does not"
						" exist in database") % attachName)
					attachablesExist = False
			else:
				try:
					api.getChannel(attachName,API_SERVER)
				except api.APIWarningException:
					print(("Error: channel %s referenced in CSV does "
						"not exist in database") % attachName)
					attachablesExist = False
	
	if not attachablesExist:
		print(("CSV file contains references to moments or channels "
			"not found in the database."))
		print("Please remove these references and rerun the program.")
		quit()
	
	newUploads = 0
	failedUploads = 0
	#upload new images
	for name,url,desc in albumList:
		s3Filepath = str(s3Folder.joinpath(name+'.jpg'))
		s3URL = "https://%s.s3.amazonaws.com/%s" % \
			(S3_BUCKET,s3Filepath)
		
		print(s3URL)
		
		if desc is not None:
			mID = api.mediaDataUpload(s3URL,name,mission,
				API_SERVER,API_SERVER_TOKEN,
				description=desc)
		else:
			mID = api.mediaDataUpload(s3URL,name,mission,
				API_SERVER,API_SERVER_TOKEN)
		
		#upload image to S3
		if mID is not None:
			newUploads+=1
			imgResponse = requests.get(url,stream=True)
			if imgResponse.ok:
				with imgResponse.raw as f:
					s3Upload(f,S3_BUCKET,s3Filepath)
			else:
				print(imgResponse.status_code,imgResponse.text)
		else:
			failedUploads+=1
		
		#add id to list of media attachments
		if name in attachables and mID is not None:
			existingMediaIDs[name] = mID
		
	#add media attachments
	for name, mID in existingMediaIDs.items():
		for attachType,attachName,metStart,metEnd in attachables[name]:
			if metStart is None:
				api.mediaAttachableUpload(mID,attachType,
					attachName,API_SERVER,API_SERVER_TOKEN)
			else:
				api.mediaAttachableUpload(mID,attachType,
					attachName,API_SERVER,API_SERVER_TOKEN,
					met_start=metStart,met_end=metEnd)
	
	print("Completed.")
	if newUploads > 0:
		print("%d new images uploaded." % newUploads)
	if failedUploads > 0:
		print(("%d images failed to upload.  Check error messages "
			"- 'title has already been taken' likely means the image "
			"already exists in system and is not an issue") \
			% failedUploads) 
		
