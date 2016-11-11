import glob;
import os;
import ntpath;
import wave
import contextlib
import math


def GetFileTime(Filename):
    fname = Filename;
    with contextlib.closing(wave.open(fname,'r')) as f:
        frames = f.getnframes()
        rate = f.getframerate()
        duration = frames / float(rate)
        duration = math.ceil(duration * 1000.0)
        return duration;


def UploadFile(mission, recorder, channel, metstart, metduration, currfile):
            met_end = int(metstart)+int(metduration);
            met_end = str(met_end).zfill(11)
            met_start = metstart;
            slug = '';
            title = '';
            url = "https://s3.amazonaws.com/exploreapollo-data/audio/A11_HR1U_CH10_AIR2GND/" + currfile + ".wav";
            #print("met_end : " + str(int(met_end)) + "\nmet_start : " + str(int(met_start)) + "\nslug : " + slug + "\ntitle : " + title + "\nurl : " + url );

def TranscribeTrs(StartTime, EndTime, Text, Speaker, Met):
            met_end = int(Met) + float(EndTime)*1000;
            met_start = int(Met) + float(StartTime)*1000;
            met_end =  str(met_end).zfill(11)
            met_start = str(met_start).zfill(11)
            #print("\nmet_end : " + str(int(met_end)) + "\nmet_start : " + str(int(met_start)) + "\nText " + Text);
            
WavFilesWithExe = glob.glob('.\A11_HR1U_CH10_AIR2GND\*.wav');
TrsFilesWithExe = glob.glob('.\A11_HR1U_CH10_AIR2GND\*.txt');
WavFiles = [];
TrsFiles = [];

Channel = "AIR2GND";

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
 
for CurrentFile in WavFiles:
    if(CurrentFile in TrsFiles):#checks if the files match up
        VarArray = CurrentFile.split("_");
        if (len(VarArray) == 4) :
                    #print("\nFile : " + CurrentFile);
                    filewav = '.\A11_HR1U_CH10_AIR2GND\\'+CurrentFile+'.wav';
                    UploadFile(VarArray [0], VarArray [1], VarArray [2], VarArray [3],GetFileTime(filewav) , CurrentFile);
                    filetext = '.\A11_HR1U_CH10_AIR2GND\\'+CurrentFile+'.txt';
                    with open(filetext) as f:
                        content = f.readlines();
                        for lines in content:
                                LineArray = lines.split("\t");
                                TranscribeTrs(LineArray[1],LineArray[2],LineArray[3],LineArray[4], VarArray[3]);
                        #print(content);
        # file format : A11_HR1U_CH10_00651360000.wav
        #VarArray [0] = A11 - Apollo 11
        #VarArray [1] = HR1U - Historical Recorder 1 upper
        #VarArray [2] = CH20 - Channel 20
        #VarArray [3] = 00651360000 MET in m sec 
                
        
