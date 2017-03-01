import requests
import os.path
import subprocess

PEOPLE_API          = 'api/people'
TRANSCRIPT_ITEM_API = 'api/transcript_items'
AUDIO_SEGMENT_API   = 'api/audio_segments'


def _constructURL(server,path):
	'''construct a complete URL from a server location and request path'''
	if server[-1] == '/' and path[0] != '/':
		return server + path
	elif server[-1] == '/' and path[0] == '/':
		return server + path[1:]
	elif server[-1] != '/' and path[0] != '/':
		return server + '/' + path
	else:
		return server + path


_personIndex = None
def getPerson(name,server,token):
	'''get the ID of the referenced name
	returns None if not found.'''
	global _personIndex
	if _personIndex is None:
		response = requests.get(_constructURL(server,PEOPLE_API))
		if response.ok:
			_personIndex = {item['name']:item['id'] for item \
				in response.json()}
		else:
			print("Failed to connect to API server.")
			return None
			
	if name in _personIndex:
		return _personIndex[name]
	else:
		_personIndex[name] = personUpload(name,server,token)
		return _personIndex[name]


def personUpload(name,server,token):
	'''put a new dummy person in the API server, return ID'''
	headers = {'Authorization':"Token token=%s" % token,
		'content-type':'application/json'}
	
	json = {
		"name" : name,
		"title" : "%s-dummy" % name,
		"photo_url" : "exploreapollo.com",
	}
	response = requests.post(_constructURL(server,PEOPLE_API),
		json=json,headers=headers)
	if response.ok:
		return response.json()['id']
	else:
		return None


def _sToMs(s):
	'''convert seconds into ms'''
	return int(float(s)*1000)


def _isNum(numCandidate):
	try:
		float(numCandidate)
		return True
	except ValueError:
		return False


def _getFileLengthMs(filepath):
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


_FORM0 = 0 #stMEt, text, duration, speaker
_FORM1 = 1 #stMet, endMet, text, speaker
def _inferFormat(f):
	'''obtain the file format of fileobject f
	return -1 if cannot be inferred'''
	for line in f:
		toks = [t.strip() for t in line.split('\t')]
		form0 = _isNum(toks[3])
		form1 = _isNum(toks[2])
		
		if form0 and not form1:
			return _FORM0
		elif not form0 and form1:
			return _FORM1
	return -1



def _parseTranscriptLine(line,lineFormat,fileMetStart,server,token):
	'''infer the line format and return startMet, endMet, text, speaker
	return None on error'''
	tok = [t.strip() for t in line.split('\t')]
	if len(tok) != 5:
		return None
	elif lineFormat == _FORM0:
		stMet   = _sToMs(tok[1]) + fileMetStart
		endMet  = _sToMs(tok[3]) + stMet
		text    = tok[2]
		spkID   = getPerson(tok[4].strip('"'),server,token)
		return (stMet, endMet, text, spkID)
	elif lineFormat == _FORM1:
		stMet   = _sToMs(tok[1]) + fileMetStart
		endMet  = _sToMs(tok[2]) + fileMetStart
		text    = tok[3]
		spkID   = getPerson(tok[4].strip('"'),server,token)
		return (stMet, endMet, text, spkID)
	else:
		return None
	


def transcriptUpload(filepath,channel,fileMetStart,server,token,
		propName=None):
	'''Parse and upload the transcript items to API server
	When propname is not None, it is used in error output
	rather than filepath
	'''
	if propName is None:
		propName = filepath
	headers = {'Authorization':"Token token=%s" % token,
		'content-type':'application/json'}
	
	with open(filepath) as f:
		lineFormat = _inferFormat(f)
		f.seek(0)
		for lineNo, line in enumerate(f):
			items = _parseTranscriptLine(line,lineFormat,fileMetStart,
				server,token)
			if items is None and len(line.split('\t')) == 0:
				continue
			elif items is None:
				pass
				##TODO - log error.
			else:
				startMet, endMet, text, personID = items

			json = {
				"text"      : text,
				"met_start" : startMet,
				"met_end"   : endMet,
				"person_id" : personID,
				"channel_id": channel,
				}
			response = requests.post(_constructURL(server,
				TRANSCRIPT_ITEM_API),json=json,headers=headers)
			if response.ok:  ###TODO - add error condition pertaining to token authentication
				pass
			else:
				print("Failed transcript %s:%d\n\t%s\n\t%s %s %s" % \
					(propName, lineNo+1, line, \
					response.status_code, \
					response.reason, \
					response.text))


def audioDataUpload(filepath,s3URL,channel,fileMetStart,server,token):
	'''upload audio segment data to API server.  does NOT upload audio file'''
	fileMetEnd   = fileMetStart + _getFileLengthMs(filepath)
	headers = {'Authorization':"Token token=%s" % token,
		'content-type':'application/json'}
	
	json = {
		"title"      : os.path.split(s3URL)[1],
		"url"        : s3URL,
		"met_start"  : fileMetStart,
		"met_end"    : fileMetEnd,
		"channel_id" : channel,
	}
	response =requests.post(_constructURL(server,AUDIO_SEGMENT_API),
		json=json,headers=headers)
	if response.ok:
		pass
	else:
		print("Failed audio segment %s\n\t%s %s %s" % \
			(filepath, response.status_code, response.reason, \
			response.text))
