import pathlib
import boto3
import sys
import os
from config import *
from utils.APIConn import *
from utils.utils import *


_s3Client = None
def s3Upload(filename,bucket,destfile):
	'''Put a file in s3.'''
	global _s3Client
	if _s3Client is None:
		_s3Client = boto3.client('s3',
			aws_access_key_id=AWS_ACCESS_KEY,
			aws_secret_access_key=AWS_SECRET_KEY,
		)
	_s3Client.upload_file(filename,bucket,destfile)


#### ####
if __name__ == "__main__":
	if len(sys.argv) != 3:
		print("Usage: python %s <local base folder> <S3 base folder>" % sys.argv[0])
		quit()
	else:
		localFolder = sys.argv[1]
		s3Folder = pathlib.Path(sys.argv[2])
	
	wavFiles = set(os.path.splitext(str(i))[0] for i \
		in pathlib.Path(localFolder).glob("**/*.wav"))
	trsFiles = set(os.path.splitext(str(i))[0] for i \
		in pathlib.Path(localFolder).glob("**/*.txt"))
	
	filesToProcess = wavFiles & trsFiles
	wavMissingTrs = wavFiles - trsFiles
	trsMissingWav = trsFiles - wavFiles
	
	for i in filesToProcess:
		print(i)
	
	if len(wavMissingTrs) > 0:
		print("These .wav files are missing corresponding .txt files and will be skipped:")
		for i in wavMissingTrs:
			print("\t%s.wav" % i)
	if len(trsMissingWav) > 0:
		print("These .txt files are missing corresponding .wav files and will be skipped:")
		for i in trsMissingWav:
			print("\t%s.txt" % i)
	
	for filepath in filesToProcess:
		txtFilepath = "%s.txt" % filepath
		wavFilepath = "%s.wav" % filepath
		
		s3TxtFilepath = s3Folder.joinpath(pathlib.Path(txtFilepath) \
			.relative_to(localFolder))
		s3WavFilepath = s3Folder.joinpath(pathlib.Path(wavFilepath) \
			.relative_to(localFolder))
		
		#s3 upload
		s3Upload(txtFilepath,S3_BUCKET,str(s3TxtFilepath))
		s3Upload(wavFilepath,S3_BUCKET,str(s3WavFilepath))
		
		#API server upload
		s3WavURL = "https://%s.s3.amazonaws.com/%s" % \
			(S3_BUCKET,s3WavFilepath)
		
		mission,recorder,channel,metstart = filenameToParams(wavFilepath)
		transcriptUpload(txtFilepath,channel,metstart,
			API_SERVER,API_SERVER_TOKEN)
		audioDataUpload(wavFilepath,s3WavURL,channel,metstart,
			API_SERVER,API_SERVER_TOKEN)




