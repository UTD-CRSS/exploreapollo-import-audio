import requests
import os.path
import subprocess
import sys

MISSION_API         = 'api/missions'
PEOPLE_API          = 'api/people'
AUDIO_SEGMENT_API   = 'api/audio_segments'
TRANSCRIPT_ITEM_API = 'api/transcript_items'
TRANSCRIPT_ITEM_SEARCH_API = 'api/transcript_items/search'
AUDIO_SEGMENT_SEARCH_API = 'api/audio_segments/search'
MEDIA_API           = 'api/media'
MEDIA_ATTACH_API    = 'api/media_attachments'
CHANNEL_API         = 'api/channels'
STORY_API			= 'api/stories'
MOMENT_API			= 'api/moments'
METRIC_API			= 'api/metrics'



#### Exceptions ####
class APIFatalException(Exception):
	def __init__(self,reason):
		self.reason = reason
	
	def __str__(self):
		return str(self.reason)

class APIWarningException(Exception):
	def __init__(self,reason):
		self.reason = reason
	
	def __str__(self):
		return str(self.reason)



def _raiseUploadException(response,location):
	'''raise the appropriate exception for an error code'''
	if response.ok:
		return
	if response.status_code == 401:
		raise APIFatalException(
			"%s - 401 Authorization failed, check API server token" % \
			location)
	else:
		raise APIWarningException("%s - %d %s" % (location,
			response.status_code,response.text)) 


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


def _extractNumber(strnum):
	'''obtain the first integer found in strnum'''
	stidx = 0
	while stidx < len(strnum) and strnum[stidx] not in '0123456789':
		stidx+=1
	endidx = stidx
	while endidx < len(strnum) and strnum[endidx] in '0123456789':
		endidx+=1
	if endidx>stidx:
		return int(strnum[stidx:endidx])
	else:
		return None


_missionIndex = None
def getMission(name,server):
	'''get the ID of the mission'''
	global _missionIndex
	if _missionIndex is None:
		try:
			response = requests.get(_constructURL(server,MISSION_API))
		except requests.exceptions.ConnectionError:
			raise APIFatalException("Failed to connect to server at %s" % server)
		if response.ok:
			_missionIndex = {_extractNumber(i['name']):i['id'] for \
				i in response.json()}
		else:
			raise APIFatalException("Failed to collect existing mission IDs")
	
	missionNo = _extractNumber(name)
	if missionNo in _missionIndex:
		return _missionIndex[missionNo]
	else:
		raise APIWarningException("No matching mission found for %s" % name)
		##TODO - mission upload, or user intervention.


_channelIndex = None
def getChannel(name,server):
	'''get the ID of a channel
	channel is uniquely identified by name'''
	global _channelIndex
	if _channelIndex is None:
		try:
			response = requests.get(_constructURL(server,CHANNEL_API))
		except requests.exceptions.ConnectionError:
			raise APIFatalException("Failed to connect to server at %s" % server)
		if response.ok:
			_channelIndex = {i['title']:i['id'] for i in response.json()}
		else:
			raise APIFatalException("Failed to collect existing channel IDs")
	
	if name in _channelIndex:
		return _channelIndex[name]
	else:
		raise APIWarningException("No matching channel found for %s" % name)



_momentIndex = None
def getMoment(name,server):
	'''get the ID of a moment
	moments are uniquely identified by their title'''
	global _momentIndex
	if _momentIndex is None:
		try:
			response = requests.get(_constructURL(server,MOMENT_API))
		except requests.exceptions.ConnectionError:
			raise APIFatalException("Failed to connect to server at %s" % server)
		if response.ok:
			_momentIndex = {i['title']:i['id'] for i in response.json()}
		else:
			raise APIFatalException("Failed to collect existing moment IDs")
	
	if name in _momentIndex:
		return _momentIndex[name]
	else:
		raise APIWarningException(
			"No matching moment found with name %s" % name)
	

_personIndex = None
def getPerson(name,server,token):
	'''get the ID of the referenced name
	returns None if not found.'''
	global _personIndex
	if _personIndex is None:
		try:
			response = requests.get(_constructURL(server,PEOPLE_API))
		except requests.exceptions.ConnectionError:
			raise APIFatalException("Failed to connect to server at %s" % server)
		
		if response.ok:
			_personIndex = {item['name']:item['id'] for item \
				in response.json()}
		else:
			raise APIFatalException("Failed to collect existing person IDs")
			
	if name in _personIndex:
		return _personIndex[name]
	else:
		_personIndex[name] = personUpload(name,server,token)
		return _personIndex[name]


_mediaIndex = None
def getMedia(name,server,token):
	'''obtain the ID of an existing media item or raise an exception
	if not found.'''
	global _mediaIndex
	if _mediaIndex is None:
		try:
			response = requests.get(_constructURL(server,MEDIA_API))
		except requests.exceptions.ConnectionError:
			raise APIFatalException("Failed to connect to server at %s" % server)
		
		if response.ok:
			_mediaIndex = {item['title']:item['id'] for item \
				in response.json()}
		else:
			raise APIFatalException("Failed to collect existing media IDs")
	
	if name in _mediaIndex:
		return _mediaIndex[name]
	else:
		raise APIWarningException(
			"No matching media found with name %s" % name)
		

def getStory(title,server,token):
	'''
		get the ID of the referenced story name
		returns None if not found.
	'''
	storyIndex = {}
	
	try:
		response = requests.get(_constructURL(server,STORY_API))
	except requests.exceptions.ConnectionError:
		raise APIFatalException("Failed to connect to server at %s" % server)
		
	if response.ok:
		storyIndex = {item['title']:item['id'] for item \
			in response.json()}
	else:
		raise APIFatalException("Failed to collect existing story IDs")
			
	if title in storyIndex:
		return storyIndex[title] #return ID of story
	else:
		return None


def getTranscriptItems(met_start, met_end, server, token):
	'''
		get all Transcript items with met_start times from 
		(met_start, met_end) 
	'''

	headers = {'Authorization':"Token token=%s" % token,
		'content-type':'application/json'}
	
	json = {
		"met_start":	met_start,
		"met_end"  :	met_end,
	}

	try:
		response = requests.get(_constructURL(server, TRANSCRIPT_ITEM_SEARCH_API),
			params=json,headers=headers)
	except requests.exceptions.ConnectionError:
		raise APIFatalException("Failed to connect to server at %s" % server)

	if response.ok:
		return response.json() 
	else:
		raise APIFatalException("Failed to collect existing transcript items")	


def getAudioSegments(met_start, met_end, server, token):
	'''
		get all audio segement items with met_start times from
		(met_start, met_end)
	'''
	headers = {'Authorization':"Token token=%s" % token,
		'content-type':'application/json'}
	
	json = {
		"met_start":	met_start,
		"met_end"  :	met_end,
	}

	try:
		response = requests.get(_constructURL(server, AUDIO_SEGMENT_SEARCH_API),
			params=json,headers=headers)
	except requests.exceptions.ConnectionError:
		raise APIFatalException("Failed to connect to server at %s" % server)

	if response.ok:
		return response.json() 
	else:
		print (response)
		raise APIFatalException("Failed to collect existing audio segments")
	

def personUpload(name,server,token):
	'''put a new dummy person in the API server, return ID'''
	headers = {'Authorization':"Token token=%s" % token,
		'content-type':'application/json'}
	
	json = {
		"name" : name,
		"title" : "%s-dummy" % name,
	}
	try:
		response = requests.post(_constructURL(server,PEOPLE_API),
			json=json,headers=headers)
	except requests.exceptions.ConnectionError:
		raise APIFatalException("Failed to connect to server at %s" % server)
	
	if response.ok:
		return response.json()['id']
	else:
		_raiseUploadException(response,"Person upload")


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
			try:
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
				if not response.ok:
					_raiseUploadException(response, "Transcript item")
			
			except APIWarningException as e:
				print("ERROR - Transcript item, %s:%d  %s" % (
					propName,lineNo+1,e.reason),file=sys.stderr)
			except requests.exceptions.ConnectionError:
				raise APIFatalException("Failed to connect to server at %s" % \
					server)
			except APIFatalException as e:
				raise e


def audioDataUpload(filepath,s3URL,channel,fileMetStart,server,token):
	'''upload audio segment data to API server.  does NOT upload audio file'''
	fileMetEnd = fileMetStart + _getFileLengthMs(filepath)
	headers = {'Authorization':"Token token=%s" % token,
		'content-type':'application/json'}
	
	json = {
		"title"      : os.path.split(s3URL)[1],
		"url"        : s3URL,
		"met_start"  : fileMetStart,
		"met_end"    : fileMetEnd,
		"channel_id" : channel,
	}
	try:
		response = requests.post(_constructURL(server,AUDIO_SEGMENT_API),
			json=json,headers=headers)
	except requests.exceptions.ConnectionError:
		raise APIFatalException("Failed to connect to server at %s" % server)
	if not response.ok and response.status_code == 401:
		raise APIFatalException(
			"Audio data - 401 Authorization failed, check API server token")
	elif not response.ok:
		print("ERROR - Audio segment, %s  %d %s" % (
			s3URL,response.status_code,response.text),
			file=sys.stderr) 


_MEDIA_ALLOWED_PARAMS=['description','caption','alt_text','type']
def mediaDataUpload(url,title,mission,server,token,**kwargs):
	'''upload media data.  Does NOT upload media itself
	allowed kwargs - description,caption,alt_text,type'''
	headers = {'Authorization':"Token token=%s" % token,
		'content-type':'application/json'}
	
	json = {
		"url"        : url,
		"title"      : title,
		"mission_id" : getMission(mission,server),
	}
	
	for jhead, jval in kwargs.items():
		if jhead in _MEDIA_ALLOWED_PARAMS:
			json[jhead] = jval
	
	try:
		response = requests.post(_constructURL(server,MEDIA_API),
			json=json,headers=headers)
	except requests.exceptions.ConnectionError:
		raise APIFatalException("Failed to connect to server at %s" % server)
	if not response.ok and response.status_code == 401:
		raise APIFatalException(
			"Media data - 401 Authorization failed, check API server token")
	elif not response.ok:
		print("ERROR - Media data, %s  %d %s" % (
			url,response.status_code,response.text),
			file=sys.stderr) 
	else:
		return response.json()['id']
	

_MATTACH_ALLOWED_PARAMS = set(['met_start','met_end'])
def mediaAttachableUpload(mediaId,attachableType,attachableName,
		server,token,**kwargs):
	'''Connect an existing media upload to a moment or channel.
	IDs are IDs as represented in database
	attachableType must be 'Channel' or 'Moment'
	allowed kwargs are met_start, met_end'''
	headers = {'Authorization':"Token token=%s" % token,
		'content-type':'application/json'}
	
	if attachableType == 'Channel':
		attachableId = getChannel(attachableName,server)
	elif attachableType == 'Moment':
		attachableId = getMoment(attachableName,server)
	else:
		raise APIWarningException("Unrecognized attachable type %s" % str(attachableType))
	
	json = {
		"media_id"              : mediaId,
		"media_attachable_type" : attachableType,
		"media_attachable_id"   : attachableId,
	}
  
  
	for jhead, jval in kwargs.items():
		if jhead in _MATTACH_ALLOWED_PARAMS:
			json[jhead] = jval
	
	try:
		response = requests.post(_constructURL(server,MEDIA_ATTACH_API),
			json=json, headers=headers)
	except requests.exceptions.ConnectionError:
		raise APIFatalException("Failed to connect to server at %s" % server)
	if not response.ok and response.status_code == 401:
		raise APIFatalException(
			"Media data - 401 Authorization failed, check API server token")
	elif not response.ok:
		print("ERROR - Media data, %s  %d %s" % (
			mediaId,response.status_code,response.text),
			file=sys.stderr) 


def upload_moment(momentTitle, momentDescription, met_start, met_end, channel_id, story_id, server, token):
	'''
		upload a moment
	'''
	headers = {'Authorization':"Token token=%s" % token,
		'content-type':'application/json'}

	json = {
		"title"			:	momentTitle,
		"description"	:	momentDescription,
		"met_start"		:	met_start,
		"met_end"		:	met_end,
		"channel_ids"	:	[channel_id],
		"story_ids"		:	[story_id],  
	}


	try:
		response = requests.post(_constructURL(server,MOMENT_API),
			json=json,headers=headers)
		if not response.ok:
			_raiseUploadException(response, "Moment")
	except APIWarningException as e:
		print("ERROR - Moment, %s  %s" % (momentTitle, e.reason),file=sys.stderr)
	except requests.exceptions.ConnectionError:
		raise APIFatalException("Failed to connect to server at %s" % server)
	except APIFatalException as e:
		raise e


def upload_story(storyTitle, storyDescription, server, token):
	'''
		uploads a story with storyTitle, storyDescription,
		and empty moment_ids. Returns story_id so moments uploaded
		later in script can use this to be associated with the story.

		returns storyID = -1 if error uploading story 
	'''

	headers = {'Authorization':"Token token=%s" % token,
		'content-type':'application/json'}

	json = {
		"title"			:	storyTitle,
		"description"	:	storyDescription,
		"moment_ids"	:	[],
	}

	storyID = -1
	try:
		response = requests.post(_constructURL(server,STORY_API),
			json=json,headers=headers)
		if not response.ok:
			_raiseUploadException(response, "Story")
		else:
			storyID = response.json()["id"]	
	except APIWarningException as e:
		print("ERROR - STORY, %s  %s" % (storyTitle, e.reason),file=sys.stderr)
		raise e
	except requests.exceptions.ConnectionError:
		raise APIFatalException("Failed to connect to server at %s" % server)
	except APIFatalException as e:
		raise e
    
	return storyID


def upload_metric(Type, met_start, met_end, channel_id, data, server,token):
	'''
		uploads a metric with type (string, currently not related to subclass of metric WordCount),
		met_start, met_end, channelID, data (a dict containing unstructured data. cannot have nested
		structures. one key -> one string)
	'''

	headers = {'Authorization':"Token token=%s" % token,
		'content-type':'application/json'}

	json = {
		"metric"	:{
						"type"		: Type, 
						"met_start"	: met_start,
						"met_end"	: met_end,
						"channel_id": channel_id,
						"data"		: data,
					  }
	}


	try:
		response = requests.post(_constructURL(server,METRIC_API),
			json=json,headers=headers)
		if not response.ok:
			_raiseUploadException(response, "Metric")
	except APIWarningException as e:
		print("ERROR - Metric, %s  %s" % (Type, e.reason),file=sys.stderr)
	except requests.exceptions.ConnectionError:
		raise APIFatalException("Failed to connect to server at %s" % server)
	except APIFatalException as e:
		raise e
