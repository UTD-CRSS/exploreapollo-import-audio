import glob;
import os;
import ntpath;


def UploadFile(mission, recorder, channel, met):
            print("Mission : " + mission + "\nRecorder : " + recorder + "\nChannel : " + channel + "\nMET : " + met );
        
            
WavFilesWithExe = glob.glob('.\A11_HR1U_CH10_AIR2GND\*.wav');
TrsFilesWithExe = glob.glob('.\A11_HR1U_CH10_AIR2GND\*.txt');
WavFiles = [];
TrsFiles = [];



#used to take the extension out of the file
for CurrentFile in WavFilesWithExe:
    curFile = ntpath.basename(CurrentFile);
    filename,fileext = os.path.splitext(curFile);
    WavFiles.append(filename);
    
#used to take the extension out of the file
for CurrentFile in TrsFilesWithExe:
    curFile = ntpath.basename(CurrentFile);
    filename,fileext = os.path.splitext(curFile);
    TrsFiles.append(filename);

print(TrsFiles[2])    
for CurrentFile in WavFiles:
    if(CurrentFile in TrsFiles):#checks if the files match up
        VarArray = CurrentFile.split("_");
        if (len(VarArray) == 4) :
                    print("File : " + CurrentFile);
                    UploadFile(VarArray [0], VarArray [1], VarArray [2], VarArray [3]);
        # file format : A11_HR1U_CH10_00651360000.wav
        #VarArray [0] = A11 - Apollo 11
        #VarArray [1] = HR1U - Historical Recorder 1 upper
        #VarArray [2] = CH20 - Channel 20
        #VarArray [3] = 00651360000 MET in m sec 
                
        
