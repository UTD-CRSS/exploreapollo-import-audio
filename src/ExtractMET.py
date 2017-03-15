'''
This script extracts met times for images from 
https://www.hq.nasa.gov/alsj/a11/images11.html.

This script should not be expected to work
for any other page. 
'''

from html.parser import HTMLParser
from queue import LifoQueue
import sys
import re

def toMet(missionTime):
	hours = int(missionTime[0:3])
	minutes = int(missionTime[4:6])
	seconds = int(missionTime[7:9])
	
	totsecs = (hours * 60 + minutes) * 60 + seconds
	return totsecs * 1000


class MetExtractor(HTMLParser):
	
	def __init__(self):
		HTMLParser.__init__(self)
		self._activeRegion = False
		self._tagStack = LifoQueue()
		self.idRegex = re.compile('AS\d{2}-\d{2}-\d{4}')
		self.timeRegex = re.compile('\d{3}:\d{2}:\d{2}')
	
	
	def handle_starttag(self,tag,attrs):
		attrDict = {i:j for i,j in attrs}
		self._tagStack.put((tag,attrDict))
		
		if not self._activeRegion and tag == 'a' and 'name' in attrDict:
			if attrDict['name'] == 'Mission':
				self._activeRegion = True
		elif self._activeRegion and tag == 'a' and 'name' in attrDict:
			if attrDict['name'] == 'Post':
				self._activeRegion = False
	
	
	def handle_endtag(self,tag):
		self._tagStack.get()
		
	
	def handle_data(self,data):
		if self._tagStack.empty():
			return
		
		curtag,curattrs = self._tagStack.get()
		self._tagStack.put((curtag,curattrs))
		
		if self._activeRegion and curtag != 'a':
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
