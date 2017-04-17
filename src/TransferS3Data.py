import boto3
import os
from config import *
from utils.utils import *
import utils.APIConn as APIConn
import sys


if __name__ == "__main__":
	if len(sys.argv) == 1:
		target_channel = met_min = met_max = None
	elif len(sys.argv) == 4:
		target_channel   = int(sys.argv[1])
		met_min = int(sys.argv[2])
		met_max   = int(sys.argv[3])
	else:
		print("Usage: %s [channel met_min met_max]" % sys.argv[0])
		quit()
	
	
	s3 = boto3.session.Session(aws_access_key_id=AWS_ACCESS_KEY,
		aws_secret_access_key=AWS_SECRET_KEY).resource('s3')
	bucket = s3.Bucket(S3_BUCKET)

	objcollection = {} #objcollection['fname_no_ext'] = (txtobj,wavobj)
	
	for obj in bucket.objects.all():
		name,ext = os.path.splitext(obj.key)
		if name in objcollection and ext == '.txt':
			objcollection[name][0] = obj
		elif name in objcollection and ext == '.wav':
			objcollection[name][1] = obj
		elif ext == '.txt':
			objcollection[name] = [obj,None]
		elif ext == '.wav':
			objcollection[name] = [None,obj]


	for name, fileobjs in objcollection.items():
		txt, wav = fileobjs
		
		if txt is None or wav is None:
			continue
		
		mission, recorder, channel, fileMetStart = filenameToParams(txt.key)
		
		if met_max is not None and \
			(fileMetStart > met_max or fileMetStart < met_min or\
			channel != target_channel):
			continue
		
		bucket.download_file(txt.key,'tmp.txt')
		bucket.download_file(wav.key,'tmp.wav')
		
		APIConn.transcriptUpload('tmp.txt',channel,fileMetStart,
			API_SERVER,API_SERVER_TOKEN,txt.key)
		APIConn.audioDataUpload('tmp.wav',
			"https://%s.s3.amazonaws.com/%s" % (S3_BUCKET,wav.key),
			channel,fileMetStart,API_SERVER,API_SERVER_TOKEN)
		

		
		
	
	
