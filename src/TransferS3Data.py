import boto3
import os
import requests
import subprocess
from config import *

HEADERS = {'Authorization':"Token token=%s" % API_SERVER_TOKEN,
	'content-type':'application/json'}


def sToMs(s):
	'''convert seconds into ms'''
	return int(float(s)*1000)



def getFileLengthMs(filepath):
	'''get the length of a wav file in ms'''
	res = subprocess.run(['ffmpeg','-i',filepath],stderr=subprocess.PIPE,
		universal_newlines=True)
	for line in res.stderr.split('\n'):
		if "Duration" in line:
			timestr = line.split()[1]
			hour, minute, sec = map(lambda s:float(s.strip(',')),timestr.split(':'))
			durationSec = sec + 60*(minute + 60*hour)
			
		
	return int(durationSec * 1000)



def filenameToParams(filename):
	'''convert filename to (mission, recorder, channel, fileMetStart)
	expects a format something like A11_HR1U_CH10_00651360000.txt
	'''
	cleanFilename = os.path.splitext(os.path.split(filename)[1])[0]
	mission,recorder,rchannel,rmetstart = cleanFilename.split('_')
	
	chidx = 0
	while rchannel[chidx] not in "0123456789":
		chidx += 1
	channel = int(rchannel[chidx:])
	metstart = int(rmetstart)
	
	return (mission,recorder,channel,metstart)



def transcriptUpload(filepath,mission, recorder, channel, fileMetStart):
	'''Parse and upload the transcript items to API server'''
	with open(filepath) as f:
		for lineNo, line in enumerate(f):
			lineToks = [tok.strip() for tok in line.split("\t")]
			if len(lineToks) != 5:
				continue
			startMet = sToMs(lineToks[1]) + fileMetStart
			endMet = sToMs(lineToks[3]) + startMet
			text = lineToks[2]
			speaker = lineToks[4]
			##TODO - incomplete parameters (dummy person ID).
			json = {
				"text"      : text,
				"met_start" : startMet,
				"met_end"   : endMet,
				"person_id" : 4,
				"channel_id": channel,
				}
			response = requests.post("%s/api/transcript_items" % API_SERVER,
				json=json,headers=HEADERS)
			if response.ok:
				pass
			else:
				print("Failed transcript %s:%d\n\t%s\n\t%s %s %s" % \
					(filepath, lineNo+1, line, \
					response.status_code, \
					response.reason, \
					response.text))
				
				

def audioDataUpload(filepath,s3URL,mission, recorder, channel, fileMetStart ):
	'''upload audio segment data to API server.  does NOT upload audio file'''
	fileMetEnd   = fileMetStart + getFileLengthMs(filepath)
	
	json = {
		"title"      : os.path.split(s3URL)[1],
		"url"        : s3URL,
		"met_start"  : fileMetStart,
		"met_end"    : fileMetEnd,
		"channel_id" : channel,
	}
	
	response =requests.post("%s/api/audio_segments" % API_SERVER,
		json=json,headers=HEADERS)
	if response.ok:
		pass
	else:
		print("Failed audio segment %s\n\t%s %s %s" % \
			(filepath, response.status_code, response.reason, \
			response.text))


if __name__ == "__main__":
	s3 = boto3.session.Session(aws_access_key_id=AWS_ACCESS_KEY,
		aws_secret_access_key=AWS_SECRET_KEY).resource('s3')
	bucket = s3.Bucket(S3_BUCKET)

	objcollection = {} #objcollection['filename_no_ext'] = (txtobj,wavobj)

	for obj in bucket.objects.all():
		print(obj.key)
		
		name,ext = os.path.splitext(obj.key)
		if name in objcollection and ext == '.txt':
			objcollection[name][0] = obj
		elif name in objcollection and ext == '.wav':
			objcollection[name][1] = obj
		elif ext == '.txt':
			objcollection[name] = [obj,None]
		elif ext == '.wav':
			objcollection[name] = [None,obj]


	print("Done looking through drump\n\n")

	for name, fileobjs in objcollection.items():
		print(name)
		txt, wav = fileobjs
		
		if txt is None or wav is None:
			continue
		
		mission, recorder, channel, fileMetStart = filenameToParams(txt.key)
		bucket.download_file(txt.key,'tmp.txt')
		bucket.download_file(wav.key,'tmp.wav')
		transcriptUpload('tmp.txt', mission, recorder, channel, fileMetStart)
		audioDataUpload('tmp.wav',"https://%s.s3.amazonaws.com/%s" % \
			(S3_BUCKET,wav.key), \
			mission, recorder, channel, fileMetStart)

		
		
	
	
