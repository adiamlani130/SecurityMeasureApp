#Import necessary libraries and packages
import time
from securityCode.sensorDetection import sensorDetection
from securityCode.verification import Verification
from tkinter import messagebox
import tkinter as tk
from PIL import Image, ImageTk  # For handling images
import securityCode.weatherInformation as weatherInformation
import threading
#Variable indicating status of system
def main():
 run1=None
 #Try-catch for main function
 try:
   armed=False
   #create GUI using tkinter
   root = tk.Tk()
   root.title("Security System")
   root.geometry("400x500")  # Set window size
   root.configure(bg="lightblue")
   # Add a welcome label
   welcome_label = tk.Label(root, text="Welcome to the Verification System", font=("Helvetica", 16), bg="lightblue")
   welcome_label.pack(pady=20)
   # Initialize verification state
   voiceVerified = False
   cameraVerified = False
   root.title("Weather Information")
   root.geometry()


   # Create a button for attempting spoken password verification
   def voiceButton():
     nonlocal voiceVerified  # Use nonlocal to modify the variable from the outer scope
     #Capture video of user's dialogue and upload to existing S3 bucket
     Verification.captureVideo('password.mp4',5)
     Verification.uploadToS3('password.mp4','s3BucketName')  # Call the external method, add S3 Bucket here
     passwordSpoken=Verification.transcribeAudio('s3_uri','transcriptionJobName') #MUST BE SET
     #Check if words spoken match password
     if passwordSpoken:
       voiceVerified = True
       #Reconfigure so audio password is verified
       voice_label.config(text="Voice Password: Completed", fg="green")
       voice_button.config(bg="green")
       checkVerificationStatus()  # Check if both verifications are completed
     else:
         #Incorrect password case
         voice_label.config(text="Voice Password: Did not pass", fg="red")
  
   #Create a button for conduction facial recognition
   def cameraButton():
       nonlocal cameraVerified  # Use nonlocal to modify the variable from the outer scope
       #Take image of user
       verifyIdentity= Verification()
       verifyIdentity.captureImage('sourceImage.jpg')
       result=verifyIdentity.compareFaces('sourceImage.jpg','referenceImage.jpg')
       #Check if user's face matches owner's face
       if result:
         cameraVerified = True
         camera_label.config(text="Picture Verification: Completed", fg="green")
         camera_button.config(bg="green")
         checkVerificationStatus()  # Check if both verifications are completed
       else:
         #Negative recognition case
         camera_label.config(text="Picture Verification: Did not pass", fg="red")
  
   #Check if both verification steps are complete
   def checkVerificationStatus():
     #Create 'arm' button if conditions satisfied
     if voiceVerified and cameraVerified:
       arm_button.pack(pady=20)
  
   #Camera GUI element on screen
   def updateClock(label):
     current_time = time.strftime("%H:%M:%S")  # Get the current time in HH:MM:SS format
     label.config(text=current_time)  # Update the label with the current time
     label.after(1000, updateClock, label)
   #Arm security system
   def armSystem():
     nonlocal armed  # Access the armed variable from outer scope
     # Switch status and print
     toggle()
     print("System Armed: ", armed)
     global run1
     if armed:
       run1 = sensorDetection()
       # Start sensor detection in a new thread to avoid blocking the main GUI thread
       sensor_thread = threading.Thread(target=runSensorDetection, args=(run1,))
       sensor_thread.start()
     else:
       # Safely stop the sensor system
       if 'run1' in locals():
         run1.terminate()


   #Run sensor system
   def runSensorDetection(run1):
     global armed  # Use global because this runs in a different thread
     while armed:
       run1.printSensors()
       time.sleep(5)
  
   #Switch system status
   def toggle():
     nonlocal armed
     armed= not armed
  
   #Set up voice recognition button with voice.jpg
   voice_image = Image.open("voice.jpg")  # Load the image
   voice_image = voice_image.resize((100, 100), Image.ANTIALIAS)  # Resize the image
   voice_photo = ImageTk.PhotoImage(voice_image)  # Convert image for Tkinter
   voice_button = tk.Button(root, image=voice_photo, command=voiceButton, relief="flat")
   voice_button.pack(pady=10)
   voice_label = tk.Label(root, text="Click to record voice password", font=("Helvetica", 10), bg="lightblue")
   voice_label.pack(pady=5)
   #Set up facial recognition button with camera.jpg
   camera_image = Image.open("camera.jpg")  # Load the image
   camera_image = camera_image.resize((100, 100), Image.ANTIALIAS)  # Resize the image
   camera_photo = ImageTk.PhotoImage(camera_image)  # Convert image for Tkinter
   camera_button = tk.Button(root, image=camera_photo, command=cameraButton, relief="flat")
   camera_button.pack(pady=10)
   camera_label = tk.Label(root, text="Click to take picture", font=("Helvetica", 10), bg="lightblue")
   camera_label.pack(pady=5)
   #Set up arm system button
   arm_button = tk.Button(root, text="Arm System", bg="black", fg="green", font=("Helvetica", 14), command=armSystem)
   arm_button.pack_forget()  # Hide it initially
   #Label for clock
   clock_label = tk.Label(root, font=('Helvetica', 14))
   clock_label.pack(pady=20)  # Add some vertical padding
   #Update clock
   updateClock(clock_label)


   #Change weather information for GUI
   def updateWeather():
     # Get data from API, display on screen if retrievable
     try:
       weather_info = weatherInformation.getWeatherSummary(False)
       weather_label.config(text=weather_info)
     except Exception as e:
       weather_label.config(text="Error loading weather information")
       print(f"Error: {e}")
   #Label for weather information
   weather_label = tk.Label(root, text="Loading weather...", font=('Helvetica', 12), bg="lightblue")
   weather_label.pack(pady=5)
   #Change weather summary
   updateWeather()
   #Keep running application
   root.mainloop()
 #Catch error in main
 except Exception as e:
   print(f"An error occurred in the main function: {str(e)}")
if __name__ == "__main__":
   main()
