import boto3
import os
from config import *
from utils.utils import *
from utils.APIConn import *



if __name__ == "__main__":
	s3 = boto3.session.Session(aws_access_key_id=AWS_ACCESS_KEY,
		aws_secret_access_key=AWS_SECRET_KEY).resource('s3')
	bucket = s3.Bucket(S3_BUCKET)

	objcollection = {} #objcollection['fname_no_ext'] = (txtobj,wavobj)
	
	numobjs = 0
	for obj in bucket.objects.all():
		name,ext = os.path.splitext(obj.key)
		if name in objcollection and ext == '.txt':
			objcollection[name][0] = obj
			numobjs+=1
		elif name in objcollection and ext == '.wav':
			objcollection[name][1] = obj
			numobjs+=1
		elif ext == '.txt':
			objcollection[name] = [obj,None]
		elif ext == '.wav':
			objcollection[name] = [None,obj]


	itemno = 1
	for name, fileobjs in objcollection.items():
		print("%s (%d/%d)" % (name,itemno,numobjs))
		txt, wav = fileobjs
		
		if txt is None or wav is None:
			continue
		
		mission, recorder, channel, fileMetStart = filenameToParams(txt.key)
		bucket.download_file(txt.key,'tmp.txt')
		bucket.download_file(wav.key,'tmp.wav')
		
		transcriptUpload('tmp.txt',channel,fileMetStart,
			API_SERVER,API_SERVER_TOKEN,txt.key)
		audioDataUpload('tmp.wav',
			"https://%s.s3.amazonaws.com/%s" % (S3_BUCKET,wav.key),
			channel,fileMetStart,API_SERVER,API_SERVER_TOKEN)
		
		itemno+=1

		
		
	
	
