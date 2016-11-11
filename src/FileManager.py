import glob;
import os;
import ntpath;
import wave
import contextlib
import math
import requests

def GetFileTime(Filename):
    fname = Filename;
    with contextlib.closing(wave.open(fname,'r')) as f:
        frames = f.getnframes()
        rate = f.getframerate()
        duration = frames / float(rate)
        duration = math.ceil(duration * 1000.0)
        return duration;


def UploadFile(mission, recorder, metstart, metduration, currfile):
            met_end = int(metstart)+int(metduration);
            met_end = str(met_end).zfill(11)
            met_start = metstart;
            slug = '';
            title = '';
            url = s3folderurl + currfile + ".wav";
            audiosegment['title'] = '';
            audiosegment['url'] = url;
            audiosegment['met_start'] = met_start;
            audiosegment['met_end'] = met_end;
            #r = requests.post(audiouploadurl, json = audiosegment, headers = headers)
            #print("met_end : " + met_end + "\nmet_start : " + met_start + "\nurl : " + url );

def TranscribeTrs(StartTime, EndTime, Text, Speaker, Met):
            met_end = int(Met) + float(EndTime)*1000;
            met_start = int(Met) + float(StartTime)*1000;
            met_end =  str(met_end).zfill(11)
            met_start = str(met_start).zfill(11)
            #print(peopleid[Speaker]);
            transcriptitems['text'] = Text;
            transcriptitems['met_start'] = met_start;
            transcriptitems['met_end'] = met_end;
            transcriptitems['person_id'] = peopleid[Speaker];
            #r = requests.post(transcriptuploadurl, json = transcriptitems, headers = headers)
            #print("\nmet_end : " + met_end + "\nmet_start : " + met_start + "\nText " + Text);


####User Defined Variables
s3folderurl = 'https://s3.amazonaws.com/exploreapollo-data/audio/A11_HR1U_CH10_AIR2GND/';
Folderurl =  '.\\A11_HR1U_CH10_AIR2GND\\';
Channelid = "1";
peopleid = {'SPK1':'1', 'SPK2':'2', 'SPK3':'3', 'SPK4':'4', 'SPK5':'5', 'SPK6':'6'};
headers = {'content-type': 'application/json', 'Authorization': 'Token token=exploreappollo'}
audiouploadurl = 'https://exploreapollo-api-staging.herokuapp.com/api/audio_segments';
audiosegment = {'title':'','url':'','met_start':'','met_end':'','channel_id':Channelid};
transcriptuploadurl = 'https://exploreapollo-api-staging.herokuapp.com/api/transcript_items'
transcriptitems = {'text':'', 'met_start':'', 'met_end':'', 'person_id':'','channel_id':Channelid};
###


WavFilesWithExe = glob.glob(Folderurl + '*.wav');
TrsFilesWithExe = glob.glob(Folderurl + '*.txt');
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
 
for CurrentFile in WavFiles:
    if(CurrentFile in TrsFiles):#checks if the files match up
        VarArray = CurrentFile.split("_");
        if (len(VarArray) == 4) :
                    #print("\nFile : " + CurrentFile);
                    filewav = Folderurl+CurrentFile+'.wav';
                    UploadFile(VarArray [0], VarArray [1], VarArray [3],GetFileTime(filewav) , CurrentFile);
                    filetext = Folderurl+CurrentFile+'.txt';
                    with open(filetext) as f:
                        content = f.readlines();
                        for lines in content:
                                lines1 = lines.split("\n");
                                LineArray = lines1[0].split("\t");
                                TranscribeTrs(LineArray[1],LineArray[2],LineArray[3],LineArray[4], VarArray[3]);
                        #print(content);
        # file format : A11_HR1U_CH10_00651360000.wav
        #VarArray [0] = A11 - Apollo 11
        #VarArray [1] = HR1U - Historical Recorder 1 upper
        #VarArray [2] = CH20 - Channel 20
        #VarArray [3] = 00651360000 MET in m sec 
                
        
