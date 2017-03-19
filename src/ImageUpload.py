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


def getAttachablesFromFile(filename):
	res = {}
	with open(filename,'r') as f:
		for row in csv.DictReader(f):
			mediaTitle = row['media_title']
			if mediaTitle not in res:
				res[mediaTitle] = []
			
			try:
				res[mediaTitle].append((row['attachable_type'],
					row['attachable_title'],
					int(row['met_start']),int(row['met_end'])))
			except ValueError:
				res[mediaTitle].append((row['attachable_type'],
					row['attachable_title'],
					None,None))
	
	return res



if __name__ == "__main__":
	if len(sys.argv) != 4 and len(sys.argv) != 5:
		print("Usage: %s <Flickr album id> <S3 folder> <Mission name> [media attachable csv]" % sys.argv[0])
		print('Ex: %s 0001 photo "Apollo 11"')
		quit()
	
	albumID = sys.argv[1]
	s3Folder = pathlib.Path(sys.argv[2])
	mission = sys.argv[3]
	
	if len(sys.argv) == 5:
		attachables = getAttachablesFromFile(sys.argv[4])
	else:
		attachables = {}
	
	for name,url,desc in flickr.getAlbumPhotoList(albumID,FLICKR_ACCESS_KEY):
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
		
		if name in attachables and mID is not None:
			for attachType,attachName,metStart,metEnd in attachables[name]:
				if metStart is None:
					api.mediaAttachableUpload(mID,attachType,
						attachName,API_SERVER,API_SERVER_TOKEN)
				else:
					api.mediaAttachableUpload(mID,attachType,
						attachName,API_SERVER,API_SERVER_TOKEN,
						met_start=metStart,met_end=metEnd)
		
		if mID is not None:
			imgResponse = requests.get(url,stream=True)
			if imgResponse.ok:
				with imgResponse.raw as f:
					s3Upload(f,S3_BUCKET,s3Filepath)
			else:
				print(imgResponse.status_code,imgResponse.text)
		
		
		
		
