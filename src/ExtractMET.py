'''
This script extracts met times for images from 
https://www.hq.nasa.gov/alsj/a11/images11.html.

This script should not be expected to work
for any other page, and the output should 
be manually corrected as there are natural
language annotations indicating time beyond
the ability of this simple script.
'''

from html.parser import HTMLParser
from queue import LifoQueue
import sys
import re

def toMet(missionTime):
	timeSlots = missionTime.split(':')
	
	hours = int(timeSlots[0])
	minutes = int(timeSlots[1])
	if len(timeSlots) == 3:
		seconds = int(timeSlots[2])
	else:
		seconds = 0
	
	totsecs = (hours * 60 + minutes) * 60 + seconds
	return totsecs * 1000


class MetExtractor(HTMLParser):
	EMPTY_ELEMS = set(['area','base','br','col','embed','hr','img',
		'input','link','meta','param','source','track','wbr'])
	
	def __init__(self):
		HTMLParser.__init__(self)
		self._activeRegion = False
		self._tagStack = LifoQueue()
		self.idRegex = re.compile('AS\d{2}-\d{2}-\d{4}')
		self.timeRegex = re.compile('\d+:\d{2}(:\d{2})?')
	
	
	def handle_starttag(self,tag,attrs):
		if tag in MetExtractor.EMPTY_ELEMS:
			return
		
		attrDict = {i:j for i,j in attrs}
		self._tagStack.put((tag,attrDict))
		
		if not self._activeRegion and tag == 'a' and 'name' in attrDict:
			if attrDict['name'] == 'Mission':
				self._activeRegion = True
		elif self._activeRegion and tag == 'a' and 'name' in attrDict:
			if attrDict['name'] == 'Post':
				self._activeRegion = False
	
	
	def handle_endtag(self,tag):
		if tag in MetExtractor.EMPTY_ELEMS:
			return
		
		self._tagStack.get()
		
	
	def handle_data(self,data):
		if self._tagStack.empty():
			return
		
		curtag,curattrs = self._tagStack.get()
		self._tagStack.put((curtag,curattrs))
		
		if self._activeRegion and (curtag == 'p' or curtag == 'body'):
			imgIDCandidate = data.strip()[:12]
			if self.idRegex.fullmatch(imgIDCandidate) is not None:
				sys.stdout.write('\n' + imgIDCandidate + ',')
		elif self._activeRegion and curtag == 'a':
			timeCandidate = data.strip()[:9]
			if self.timeRegex.fullmatch(timeCandidate) is not None:
				sys.stdout.write( timeCandidate + ',' + \
					str(toMet(timeCandidate)) + ',')
		



if __name__ == "__main__":
	if len(sys.argv) != 2:
		print("Usage: python %s <input file>" % sys.argv[0])
		quit()
	
	with open(sys.argv[1]) as f:
		m = MetExtractor()
		m.feed(f.read())
