#import necessary libraries and packages
import os
import re
import subprocess
import time
import uuid
import boto3
import cv2
import requests
import config


#Verification class deals with facial recognition, password verification and camera/S3 helpers
class Verification:
    #Constructor creates AWS clients; credentials come from the standard AWS chain (aws configure)
    def __init__(self, region=None):
        region = region or config.AWS_REGION
        self.rekognitionClient = boto3.client('rekognition', region_name=region)
        self.transcribeClient = boto3.client('transcribe', region_name=region)
        self.s3Client = boto3.client('s3', region_name=region)

    # ------------------------------------------------------------------ camera
    #Create an image under filename, returns True only if a fresh frame was saved
    def captureImage(self, filename, warmupFrames=10):
        # Never fall back to a stale picture from an earlier attempt
        if os.path.exists(filename):
            os.remove(filename)
        cam = cv2.VideoCapture(config.CAMERA_INDEX)
        try:
            if not cam.isOpened():
                print("Could not open webcam")
                return False
            # Webcams usually return dark frames while auto-exposure settles
            ret, frame = False, None
            for _ in range(warmupFrames):
                ret, frame = cam.read()
            if not ret or frame is None:
                print("Could not read a frame from the webcam")
                return False
            cv2.imwrite(filename, frame)
        finally:
            cam.release()
        print(f"Image captured and saved as {filename}")
        return True

    #Use cv2 to record webcam video (video only - OpenCV does not record audio)
    def captureVideo(self, fileName, duration):
        cap = cv2.VideoCapture(config.CAMERA_INDEX)
        if not cap.isOpened():
            raise RuntimeError("Could not open webcam")
        try:
            # Size the writer from the camera's real resolution, otherwise frames are silently dropped
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 640
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 480
            fps = cap.get(cv2.CAP_PROP_FPS)
            fps = fps if fps and fps > 0 else 20.0
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Save as .mp4
            out = cv2.VideoWriter(fileName, fourcc, fps, (width, height))
            try:
                start_time = time.time()
                #Take video for given duration
                while time.time() - start_time < duration:
                    ret, frame = cap.read()  # Capture frame-by-frame
                    if not ret:
                        break
                    out.write(frame)  # Write the frame to the video
            finally:
                out.release()
        finally:
            cap.release()
        print(f"Video saved as {fileName}")

    # ---------------------------------------------------------------- microphone
    #Record audio from the microphone with ALSA's arecord (preinstalled on Raspberry Pi OS)
    def captureAudio(self, fileName, duration):
        command = ["arecord", "-q", "-f", "S16_LE", "-r", "16000", "-c", "1", "-d", str(int(duration))]
        if config.AUDIO_DEVICE:
            command += ["-D", config.AUDIO_DEVICE]
        command.append(fileName)
        subprocess.run(command, check=True, timeout=duration + 10)
        print(f"Audio saved as {fileName}")

    # ----------------------------------------------------------------------- S3
    #Upload a file to the (private) S3 bucket, returns the object key
    def uploadToS3(self, fileName, bucket, objectName=None):
        objectName = objectName or os.path.basename(fileName)
        self.s3Client.upload_file(fileName, bucket, objectName)
        print(f"Uploaded {fileName} to s3://{bucket}/{objectName}")
        return objectName

    #Temporary link to a private S3 object (used for the alarm video in the SMS)
    def presignedUrl(self, bucket, objectName, expiresIn=None):
        return self.s3Client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket, 'Key': objectName},
            ExpiresIn=expiresIn or config.VIDEO_LINK_EXPIRY_SECONDS,
        )

    # ------------------------------------------------------------------- faces
    #Static method to load image
    @staticmethod
    def loadImage(path):
        with open(path, 'rb') as image_file:
            return image_file.read()

    #Compare images given as arguments for similarity
    def compareFaces(self, sourcePath, targetPath):
        # Load image bytes from both the captured image and reference image
        captured = Verification.loadImage(sourcePath)
        reference = Verification.loadImage(targetPath)
        try:
            response = self.rekognitionClient.compare_faces(
                SourceImage={'Bytes': captured},
                TargetImage={'Bytes': reference},
                SimilarityThreshold=config.FACE_SIMILARITY_THRESHOLD,
            )
        except self.rekognitionClient.exceptions.InvalidParameterException:
            # Rekognition raises this when there is no face in one of the images
            print("No face found in the picture.")
            return False
        #Respond to similarities between faces
        if response['FaceMatches']:
            print("Face match found with similarity:", response['FaceMatches'][0]['Similarity'])
            return True
        print("No face match found.")
        return False

    # ------------------------------------------------------------------- voice
    #Return transcript data
    def getTranscript(self, transcript_url):
        response = requests.get(transcript_url, timeout=30)
        response.raise_for_status()
        transcript_data = response.json()
        return transcript_data['results']['transcripts'][0]['transcript']

    #Lowercase and strip punctuation so "Open, sesame!" matches "open sesame"
    @staticmethod
    def _normalize(text):
        return " ".join(re.sub(r"[^a-z0-9\s]", " ", text.lower()).split())

    #Check for password in transcript
    def checkPassword(self, transcript, password=None):
        password = password if password is not None else config.VOICE_PASSWORD
        return self._normalize(password) in self._normalize(transcript)

    #Take English transcript from an audio file in S3 and check it for the password
    def transcribeAudio(self, bucket, objectName, mediaFormat='wav'):
        # Job names must be unique, so every attempt gets its own
        jobName = f"security-voice-{uuid.uuid4().hex}"
        self.transcribeClient.start_transcription_job(
            TranscriptionJobName=jobName,
            Media={'MediaFileUri': f"s3://{bucket}/{objectName}"},
            MediaFormat=mediaFormat,
            LanguageCode='en-US',
        )
        try:
            # Polling for job completion
            deadline = time.time() + config.TRANSCRIBE_TIMEOUT_SECONDS
            while True:
                status = self.transcribeClient.get_transcription_job(TranscriptionJobName=jobName)
                jobStatus = status['TranscriptionJob']['TranscriptionJobStatus']
                if jobStatus in ('COMPLETED', 'FAILED'):
                    break
                if time.time() > deadline:
                    print("Transcription timed out.")
                    return False
                print("Transcribing...")
                time.sleep(3)
            if jobStatus == 'COMPLETED':
                transcript_url = status['TranscriptionJob']['Transcript']['TranscriptFileUri']
                transcript = self.getTranscript(transcript_url)
                print(f"Heard: {transcript!r}")
                return self.checkPassword(transcript)
            print("Transcription failed:", status['TranscriptionJob'].get('FailureReason'))
            return False
        finally:
            try:
                self.transcribeClient.delete_transcription_job(TranscriptionJobName=jobName)
            except Exception:
                pass

    #Full voice check: record, upload, transcribe, compare
    def verifyVoice(self, bucket, duration=None):
        fileName = 'password.wav'
        self.captureAudio(fileName, duration or config.VOICE_RECORD_SECONDS)
        objectName = f"voice/{uuid.uuid4().hex}.wav"
        self.uploadToS3(fileName, bucket, objectName)
        try:
            return self.transcribeAudio(bucket, objectName)
        finally:
            # The recording contains the pass-phrase, don't leave it lying around
            try:
                self.s3Client.delete_object(Bucket=bucket, Key=objectName)
            except Exception:
                pass
            if os.path.exists(fileName):
                os.remove(fileName)

    #Full face check: take a picture and compare it with the owner's reference photo
    def verifyFace(self, referencePath=None):
        referencePath = referencePath or config.REFERENCE_IMAGE
        if not os.path.exists(referencePath):
            raise FileNotFoundError(f"Reference photo '{referencePath}' not found")
        if not self.captureImage('sourceImage.jpg'):
            return False
        return self.compareFaces('sourceImage.jpg', referencePath)
