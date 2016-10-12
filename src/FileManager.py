import glob;
import os

def UploadFile():
			print('hello');
		
			
WavFilesWithExe = glob.glob('*.jpg');
TrxFilesWithExe = glob.glob('*.jpg');
WavFiles = []
TrxFiles = [];

#used to take the extension out of the file
for CurrentFile in WavFilesWithExe:
	filename,fileext = os.path.splitext(CurrentFile);
	WavFiles.append(filename);
	
#used to take the extension out of the file
for CurrentFile in TrxFilesWithExe:
	filename, fileext = os.path.splitext(CurrentFile);
	TrxFiles.append(filename);
for CurrentFile in WavFiles:
	if(CurrentFile in TrxFiles):#checks if the files match up
		VarArray = CurrentFile.split("_");
		# file format : A11_HR1U_CH10_00651360000.wav
		#VarArray [0] = A11 - Apollo 11
		#VarArray [1] = HR1U - Historical Recorder 1 upper
		#VarArray [2] = CH20 - Channel 20
		#VarArray [3] = 00651360000 MET in m sec 

		UploadFile();
		
