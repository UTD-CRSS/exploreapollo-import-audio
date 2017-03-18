import sys
import boto3
import pathlib
import requests
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



if __name__ == "__main__":
	if len(sys.argv) != 4:
		print("Usage: %s <Flickr album id> <S3 folder> <Mission name>" % sys.argv[0])
		print('Ex: %s 0001 photo "Apollo 11"')
		quit()
	
	albumID = sys.argv[1]
	s3Folder = pathlib.Path(sys.argv[2])
	missionID = api.getMission(sys.argv[3],API_SERVER)
	
	for name,url,desc in flickr.getAlbumPhotoList(albumID,FLICKR_ACCESS_KEY):
		s3Filepath = str(s3Folder.joinpath(name+'.jpg'))
		s3URL = "https://%s.s3.amazonaws.com/%s" % \
			(S3_BUCKET,s3Filepath)
		
		print(s3URL)
		
		if desc is not None:
			api.mediaDataUpload(s3URL,name,missionID,
				API_SERVER,API_SERVER_TOKEN,
				description=desc)
		else:
			api.mediaDataUpload(s3URL,name,missionID,
				API_SERVER,API_SERVER_TOKEN)
		
		imgResponse = requests.get(url,stream=True)
		if imgResponse.ok:
			with imgResponse.raw as f:
				s3Upload(f,S3_BUCKET,s3Filepath)
		else:
			print(imgResponse.status_code,imgResponse.text)
		
		
		
		
