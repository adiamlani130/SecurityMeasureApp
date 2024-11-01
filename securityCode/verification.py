#import necessary libraries and packages
import boto3
import cv2
import time
import requests
#Verification class deals with facial recognition and password verification especially
class Verification:
    #Constructor creates AWS clients for both tasks, needs AWS account info
    def __init__(self):
        self.rekognitionClient=boto3.client('rekognition')
        self.transcribeClient = boto3.client('transcribe',
        aws_access_key_id = "",#insert your access key ID here,
        aws_secret_access_key = "",# insert your secret access key here
        region_name = "us-east-2")# region: set for MD right now"
        self.s3Client=boto3.client('s3')
   
    #Create an image under filename
    def captureImage(filename):
        #Use cv2 webcam methods
        cam = cv2.VideoCapture(0)
        ret, frame = cam.read()
        if ret:
            cv2.imwrite(filename, frame)
        cam.release()
        cv2.destroyAllWindows()  # Close OpenCV windows
        print(f"Image captured and saved as {filename}")
    
    #Static method to load image
    @staticmethod
    def loadImage(path):
        with open(path, 'rb') as image_file:
            return image_file.read()
    
    #Compare images given as arguments for similarity
    def compareFaces(sourcePath,targetPath):
        # Load image bytes from both the captured image and reference image
        captured = Verification.loadImage(sourcePath)
        reference = Verification.loadImage(targetPath)
        rekognition_client = boto3.client('rekognition')
        # Compare faces using the local image bytes
        response = rekognition_client.compare_faces(
            SourceImage={'Bytes': captured},
            TargetImage={'Bytes': reference},
            SimilarityThreshold=90  # Similarity threshold
        )
        #Respond to similarities between faces
        if response['FaceMatches']:
            print("Face match found with similarity:", response['FaceMatches'][0]['Similarity'])
            return True
        else:
            print("No face match found.")
            return False
    
    #Static method uploads files to instiantiated s3 bucket
    @staticmethod
    def uploadToS3(fileName, bucket):
        s3client = boto3.client('s3')
        objectName = fileName
        # Upload the file
        s3client.upload_file(fileName, bucket, objectName)
        # Set the object to be publicly readable
        s3client.put_object_acl(ACL='public-read', Bucket=bucket, Key=objectName)
        # Generate the URL for the uploaded file
        url = f"https://{bucket}.s3.amazonaws.com/{objectName}"
        print(f"Video uploaded and available publicly at: {url}")
        return url
    
   #Static method uses cv2 to record webcam video
    @staticmethod
    def captureVideo(fileName,duration):
        cap = cv2.VideoCapture(0)
        # Set up video writer with format and parameters
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Save as .mp4
        out = cv2.VideoWriter(fileName, fourcc, 20.0, (640, 480))
        start_time = time.time()
        #Take video for given duration
        while int(time.time() - start_time) < duration:
            ret, frame = cap.read()  # Capture frame-by-frame
            if ret:
                out.write(frame)  # Write the frame to the video
            else:
                break
        # Release everything once job is finished
        cap.release()
        out.release()
        cv2.destroyAllWindows()
        print(f"Video saved as {fileName}")
    
    #Return transcript data
    def getTranscript(self, transcript_url):
        response = requests.get(transcript_url)
        transcript_data = response.json()
        return transcript_data['results']['transcripts'][0]['transcript']
    
    #Check for password in transcript
    def checkPassword(self, transcript):
        return "password" in transcript.lower()
    
    #Take English transcript from  audio file
    def transcribeaAudio(self,s3_uri,jobName):
         #"""Starts an AWS Transcribe job and checks if the word 'password' is spoken."""
        self.transcribeClient.start_transcription_job(
            TranscriptionJobName=jobName,
            Media={'MediaFileUri': s3_uri},
            MediaFormat='mp4',  # Change depending on your audio format
            LanguageCode='en-US'
        )
        # Polling for job completion
        while True:
            status = self.transcribeClient.get_transcription_job(TranscriptionJobName=jobName)
            if status['TranscriptionJob']['TranscriptionJobStatus'] in ['COMPLETED', 'FAILED']:
                break
            print("Transcribing...")
            time.sleep(5)
        if status['TranscriptionJob']['TranscriptionJobStatus'] == 'COMPLETED':
            transcript_url = status['TranscriptionJob']['Transcript']['TranscriptFileUri']
            transcript = self.getTranscript(transcript_url)
            return self.checkPassword(transcript)
        else:
            print("Transcription failed.")
            return False
    #Image paths should be jpg's
    #MUST SET BUCKET NAME UP