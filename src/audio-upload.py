import wave
import sys
import boto3
from botocore.exceptions import NoCredentialsError
import os
from pydub import AudioSegment

ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY")
SECRET_KEY = os.environ.get("AWS_SECRET_KEY")

def upload_to_aws(local_file, bucket, s3_file):
    s3 = boto3.client('s3', aws_access_key_id=ACCESS_KEY,
                      aws_secret_access_key=SECRET_KEY)
    print(local_file)
    try:
        s3.upload_file(local_file, bucket,s3_file)
        print("Upload Successful")
        return True
    except FileNotFoundError:
        print("The file was not found")
        return False
    except NoCredentialsError:
        print("Credentials not available")
        return False

def process_audio(start, finish, directory):
    lastAudio = None

    for filename in os.listdir(directory):
        if(not lastAudio):
            lastAudio = filename
            continue
        #find the audio on the same channel
        if(filename.find(lastAudio[len(lastAudio)-9:len(lastAudio)-7])!=-1):
            #combines two 30 minute clips, as the desired ten minutes comes from both
            combinedAudio = AudioSegment.from_wav("audio/"+lastAudio)+AudioSegment.from_wav("audio/"+lastAudio)

            #selects 10 minute section
            finalAudio = combinedAudio[start*1000:finish*1000]

            #exports 5 minute halves seperately 
            finalAudio[:300*1000].export("final-audio/"+filename[0:len(filename)-7]+"_01.wav",format='wav')
            finalAudio[300*1000:].export("final-audio/"+filename[0:len(filename)-7]+"_02.wav",format='wav')
        lastAudio = filename

def file_to_channel_name(name):
    if("A08_T203_HR1U_CH07" in name):
        return "FD"
    elif("A08_T203_HR1U_CH10" in name):
        return "NTWK"
    elif("A08_T203_HR1U_CH17" in name):
        return "EECOM"
    elif("A08_T203_HR1U_CH18" in name):
        return "GNC"
    elif("A08_T204_HR2U_CH25" in name):
        return "MOCR"
    elif("A08_T204_HR2U_CH29" in name):
        return "PAO"

def file_to_params(filename):
    tape = int(filename[7])
    nugget = int(filename[len(filename)-5])
    return (tape,nugget)

#takes in the name of the s3 directory within audio as "parent_folder" parameter and the path to the local directory as "directory"
def upload_audio(parent_folder,directory):
    #Text file created for backend purposes
    text_file = open("AudioUploadOutput.txt","w")
    for filename in os.listdir(directory):
        params = file_to_params(filename)

        #takes part of the name of the audio file to determine which s3 folder the audio belongs in
        folder_name = filename[0:len(filename)-6]+file_to_channel_name(filename)

 
        s3_file = "audio/"+parent_folder+"/" + folder_name+"/"+filename
        url = "https://exploreapollo-data.s3.amazonaws.com/"+s3_file

        #string to be output to text file
        output = "[\"Lunar_Sighting\",\"%s\",2,\"%s\",1,%s,%s]" %  (url,file_to_channel_name(filename).lower(),str(params[1]),str(params[0]))

       
        #prints output to console and text_file if the upload succeeds
        if(upload_to_aws(directory+"/"+filename,'exploreapollo-data',s3_file)):
            print(output)
            text_file.write(output+",\n")
    text_file.close()
        

#process_audio(1533,2133,r'audio')

process_audio(int(sys.argv[1]),int(sys.argv[2]),sys.argv[3])
upload_audio(sys.argv[4],'final-audio')
#upload_audio("Lunar_Sighting","final-audio")



#########################################################
#                    READ ME                            #
# 1. Made to take two audio files and combine them      #
# 2. If more than two audio files or they don't have a  #
#    combined length of over 10 minutes the program will#
#    not function properly, though can serve as a base  #
#    for general audio uploading needs                  #
#########################################################
