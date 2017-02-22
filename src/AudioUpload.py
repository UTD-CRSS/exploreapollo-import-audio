import pathlib
import boto3
import sys
import os
import requests
import subprocess
from config import *



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
	#note - builtin wave library is not sufficient because it is unable
	#to handle certain wave formats.
	res = subprocess.run(['ffmpeg','-i',filepath],stderr=subprocess.PIPE,
		universal_newlines=True)
	for line in res.stderr.split('\n'):
		if "Duration" in line:
			timestr = line.split()[1]
			hour, minute, sec = map(lambda s:float(s.strip(',')),timestr.split(':'))
			durationSec = sec + 60*(minute + 60*hour)
			
		
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
	print("S3 upload, %s -> %s" % (filename,destfile))


_personIndex = None
def getPerson(name):
	'''get the ID of the referenced name
	returns None if not found.'''
	global _personIndex
	if _personIndex is None:
		response = requests.get("%s/api/people" % API_SERVER)
		if response.ok:
			_personIndex = {item['name']:item['id'] for item \
				in response.json()}
		else:
			print("Failed to connect to API server.")
			return None
			
	if name in _personIndex:
		return _personIndex[name]
	else:
		_personIndex[name] = personUpload(name)
		return _personIndex[name]


def personUpload(name):
	'''put a new dummy person in the API server, return ID'''
	json = {
		"name" : name,
		"title" : "%s-dummy" % name,
		"photo_url" : "exploreapollo.com",
	}
	response = requests.post("%s/api/people" % API_SERVER,
		json=json,headers=HEADERS)
	if response.ok:
		return response.json()['id']
	else:
		return None


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
			speaker = lineToks[4].strip('"')
			personID = getPerson(speaker)
				
			json = {
				"text"      : text,
				"met_start" : startMet,
				"met_end"   : endMet,
				"person_id" : personID,
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
		s3Upload(txtFilepath,S3_BUCKET,s3TxtFilepath)
		s3Upload(wavFilepath,S3_BUCKET,s3WavFilepath)
		
		#API server upload
		s3WavURL = "https://%s.s3.amazonaws.com/%s" % \
			(S3_BUCKET,s3WavFilepath)
		transcriptUpload(txtFilepath)
		audioDataUpload(wavFilepath,s3WavURL)




