import pathlib
import boto3
import sys
import os
import requests
import wave


#### CONFIG ####
# Amazon S3 configuration
# uploaded files end up in specified bucket,
# with key S3_BUCKET_UPLOAD_ROOT/filename
AWS_ACCESS_KEY='XXXX'
AWS_SECRET_KEY='XXXXXX'
S3_BUCKET='XXXX'
S3_BUCKET_UPLOAD_ROOT='audio/'

# API server location and access
API_SERVER='http://localhost:4060'
API_SERVER_TOKEN='exploreapollo'

################


HEADERS = {'Authorization':"Token token=%s" % API_SERVER_TOKEN,
	'content-type':'application/json'}

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
	

def sToMs(s):
	'''convert seconds into ms'''
	return int(float(s)*1000)


def getFileLengthMs(filepath):
	'''get the length of a wav file in ms'''
	with wave.open(filepath) as f:
		durationSec = f.getnframes() / float(f.getframerate())
	return int(durationSec * 1000)


_s3Client = None
def s3Upload(filename,bucket,destfile):
	'''Put a file in s3.'''
	#~ global _s3Client
	#~ if _s3Client is None:
		#~ _s3Client = boto3.client('s3',
			#~ aws_access_key_id=AWS_ACCESS_KEY,
			#~ aws_secret_access_key=AWS_SECRET_KEY,
		#~ )
	#~ _s3Client.upload_file(filename,bucket,destfile)
	print("Dummy S3 upload! %s -> %s" % (filename,destfile))


def transcriptUpload(filepath):
	'''Parse and upload the transcript items to API server'''
	mission, recorder, channel, fileMetStart = filenameToParams(filepath)
	
	with open(filepath) as f:
		for lineNo, line in enumerate(f):
			lineToks = [tok.strip() for tok in line.split("\t")]
			if len(lineToks) != 5:
				continue
			startMet = sToMs(lineToks[1]) + fileMetStart
			endMet = sToMs(lineToks[2]) + fileMetStart
			text = lineToks[3]
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
				
				

def audioDataUpload(filepath,s3URL):
	'''upload audio segment data to API server.  does NOT upload audio file'''
	
	filename = os.path.split(filepath)[1]
	
	mission, recorder, channel, fileMetStart = filenameToParams(filename)
	fileMetEnd   = fileMetStart + getFileLengthMs(filepath)
	
	json = {
		"title"      : filename,
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
	if len(sys.argv) < 2:
		print("Usage: python %s <folder>" % sys.argv[0])
		quit()
	else:
		localFolder = sys.argv[1]
	
	wavFiles = set(os.path.splitext(str(i))[0] for i \
		in pathlib.Path(localFolder).glob("*.wav"))
	trsFiles = set(os.path.splitext(str(i))[0] for i \
		in pathlib.Path(localFolder).glob("*.txt"))
	
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
		
		#s3 upload
		s3Upload(txtFilepath,S3_BUCKET,"%s%s" % \
			(S3_BUCKET_UPLOAD_ROOT,txtFilepath))
		s3Upload(wavFilepath,S3_BUCKET,"%s%s" % \
			(S3_BUCKET_UPLOAD_ROOT,wavFilepath))
		
		#API server upload
		s3WavURL = "https://%s.s3.amazonaws.com/%s%s" % \
			(S3_BUCKET,S3_BUCKET_UPLOAD_ROOT,wavFilepath)
		transcriptUpload(txtFilepath)
		audioDataUpload(wavFilepath,s3WavURL)




