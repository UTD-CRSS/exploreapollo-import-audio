import os.path


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

def list_to_json_string(origlist):
	'''takes origlist and represents it in a string as a json list 

	example: 
		origlist = ['SPK2"', 'SPK4"', 'SPK1"', 'SPK1', 'SPK3"']

		returns '['SPK2"', 'SPK4"', 'SPK1"', 'SPK1', 'SPK3"']'
	'''

	jsonListString = '['

	for element in origlist[:-1]: 
		jsonListString += '\'{0}\','.format(element)
	jsonListString+= '\'{0}\']'.format(origlist[-1]) 


	return jsonListString