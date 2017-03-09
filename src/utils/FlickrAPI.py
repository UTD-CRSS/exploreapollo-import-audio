import requests
import json
import io

FLICKR_SERVICE = 'https://api.flickr.com/services/rest'


def _flickrURL(photoDict):
	'''construct image url from loaded photo json'''
	return 'https://farm{}.staticflickr.com/{}/{}_{}.jpg'.format(
		photoDict['farm'],
		photoDict['server'],
		photoDict['id'],
		photoDict['secret'])


def getAlbumPhotoList(albumId,key):
	'''obtain a list of (name,url,description) triple for pictures in an album'''
	results = []
	
	params = {
		'format'      : 'json',
		'method'      : 'flickr.photosets.getPhotos',
		'api_key'     : key,
		'photoset_id' : albumId,
		'extras'      : 'description',
	}
	
	response = requests.get(FLICKR_SERVICE,params=params)
	if not response.ok:
		print(response.status_code,response.reason,response.text)
		return None
	
	#remove jsonFlickrApi( and ) and get raw data
	j = json.load(io.StringIO(response.text[14:-1]))
	
	if j['stat'] != 'ok':
		#error
		return None
	
	numPages = j['photoset']['pages']
	for photo in j['photoset']['photo']:
		results.append((photo['title'],_flickrURL(photo),
			photo['description']['_content']))
	
	#load data from any additional pages
	for pageNo in range(2,numPages+1):
		params['page'] = pageNo
		response = requests.get(FLICKR_SERVICE,params=params)
		if not response.ok:
			#error
			break
		
		j = json.load(io.StringIO(response.text[14:-1]))
		
		if j['stat'] != 'ok':
			#error
			break
		
		for photo in j['photoset']['photo']:
			results.append((photo['title'],_flickrURL(photo),
				photo['description']['_content']))
		
	return results
		
		
		
		
		
	
		
