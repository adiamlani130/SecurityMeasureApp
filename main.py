#Import necessary libraries and packages
import os
import queue
import threading
import time
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk  # For handling images
import config
import weatherInformation

BG = "lightblue"


class SecurityApp:
    def __init__(self, root):
        self.root = root
        self.verifier = None
        self.sensors = None
        self.sensorThread = None
        self.stopEvent = threading.Event()
        self.voiceVerified = False
        self.cameraVerified = False
        self.busy = False
        # Results from background threads; Tkinter widgets may only be touched from the main thread
        self.results = queue.Queue()

        #create GUI using tkinter
        root.title("Security System")
        root.geometry("420x620")
        root.configure(bg=BG)
        root.protocol("WM_DELETE_WINDOW", self.onClose)
        tk.Label(root, text="Welcome to the Verification System", font=("Helvetica", 16), bg=BG).pack(pady=20)

        #Set up voice recognition button with voice.jpg
        self.voiceButton = self.makeButton("voice.jpg", "Voice", self.onVoiceButton)
        self.voiceLabel = tk.Label(root, text="Click to record voice password", font=("Helvetica", 10), bg=BG)
        self.voiceLabel.pack(pady=5)
        #Set up facial recognition button with camera.jpg
        self.cameraButton = self.makeButton("camera.jpg", "Camera", self.onCameraButton)
        self.cameraLabel = tk.Label(root, text="Click to take picture", font=("Helvetica", 10), bg=BG)
        self.cameraLabel.pack(pady=5)
        #Set up arm system button (hidden until both checks pass)
        self.armButton = tk.Button(root, text="Arm System", bg="black", fg="green",
                                   font=("Helvetica", 14), command=self.toggleArmed)
        self.statusLabel = tk.Label(root, text="System: Disarmed", font=("Helvetica", 12), bg=BG)
        self.statusLabel.pack(pady=5)
        #Label for clock
        self.clockLabel = tk.Label(root, font=('Helvetica', 14))
        self.clockLabel.pack(pady=10)
        #Label for weather information
        self.weatherLabel = tk.Label(root, text="Loading weather...", font=('Helvetica', 11),
                                     bg=BG, justify="left")
        self.weatherLabel.pack(pady=5)

        self.updateClock()
        self.updateWeather()
        self.pollResults()

    #Image button if the picture exists, plain text button otherwise
    def makeButton(self, imagePath, fallbackText, command):
        if os.path.exists(imagePath):
            image = Image.open(imagePath).resize((100, 100), Image.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            button = tk.Button(self.root, image=photo, command=command, relief="flat")
            button.image = photo  # keep a reference so Tk doesn't garbage-collect it
        else:
            button = tk.Button(self.root, text=fallbackText, width=12, height=3, command=command)
        button.pack(pady=10)
        return button

    # ---------------------------------------------------------- background work
    #Run slow work (camera, AWS) off the GUI thread, then call onDone(result, error) on the GUI thread
    def runInBackground(self, work, onDone):
        def worker():
            try:
                self.results.put((onDone, work(), None))
            except Exception as e:
                self.results.put((onDone, None, e))
        threading.Thread(target=worker, daemon=True).start()

    def pollResults(self):
        while True:
            try:
                onDone, result, error = self.results.get_nowait()
            except queue.Empty:
                break
            onDone(result, error)
        self.root.after(100, self.pollResults)

    def getVerifier(self):
        if self.verifier is None:
            from verification import Verification
            self.verifier = Verification()
        return self.verifier

    # ------------------------------------------------------------ verification
    #Record the spoken password and check it with AWS Transcribe
    def onVoiceButton(self):
        if self.busy:
            return
        if not config.S3_BUCKET:
            messagebox.showerror("Setup needed", "Set S3_BUCKET (see README) before using voice verification.")
            return
        self.busy = True
        self.voiceLabel.config(text=f"Recording for {config.VOICE_RECORD_SECONDS}s... say your password", fg="black")
        self.runInBackground(lambda: self.getVerifier().verifyVoice(config.S3_BUCKET), self.onVoiceDone)

    def onVoiceDone(self, passed, error):
        self.busy = False
        if error:
            print(f"Voice verification error: {error}")
            self.voiceLabel.config(text=f"Voice Password: error ({error})", fg="red", wraplength=380)
        elif passed:
            self.voiceVerified = True
            self.voiceLabel.config(text="Voice Password: Completed", fg="green")
            self.voiceButton.config(bg="green")
            self.checkVerificationStatus()
        else:
            self.voiceLabel.config(text="Voice Password: Did not pass", fg="red")

    #Take a picture and compare it with the owner's face using AWS Rekognition
    def onCameraButton(self):
        if self.busy:
            return
        self.busy = True
        self.cameraLabel.config(text="Taking picture...", fg="black")
        self.runInBackground(lambda: self.getVerifier().verifyFace(), self.onCameraDone)

    def onCameraDone(self, passed, error):
        self.busy = False
        if error:
            print(f"Face verification error: {error}")
            self.cameraLabel.config(text=f"Picture Verification: error ({error})", fg="red", wraplength=380)
        elif passed:
            self.cameraVerified = True
            self.cameraLabel.config(text="Picture Verification: Completed", fg="green")
            self.cameraButton.config(bg="green")
            self.checkVerificationStatus()
        else:
            self.cameraLabel.config(text="Picture Verification: Did not pass", fg="red")

    #Show the 'arm'/'disarm' button once both verification steps are complete
    def checkVerificationStatus(self):
        if self.voiceVerified and self.cameraVerified:
            self.armButton.pack(pady=10, before=self.statusLabel)

    #Each arm or disarm uses up the verification, so the next one needs both checks again
    def resetVerification(self):
        self.voiceVerified = False
        self.cameraVerified = False
        self.armButton.pack_forget()
        defaultBg = self.root.cget("bg")
        self.voiceButton.config(bg=defaultBg)
        self.cameraButton.config(bg=defaultBg)
        self.voiceLabel.config(text="Click to record voice password", fg="black")
        self.cameraLabel.config(text="Click to take picture", fg="black")

    def isArmed(self):
        return self.sensorThread is not None and self.sensorThread.is_alive() and not self.stopEvent.is_set()

    # ------------------------------------------------------------------ arming
    def toggleArmed(self):
        # Never arm or disarm without a fresh voice + face verification
        if not (self.voiceVerified and self.cameraVerified):
            return
        if self.isArmed():
            self.disarm()
        elif self.sensorThread is not None and self.sensorThread.is_alive():
            return  # still shutting down from the last disarm
        else:
            self.arm()

    #Arm security system: set up sensors and start polling in a background thread
    def arm(self):
        try:
            from sensorDetection import sensorDetection
            self.sensors = sensorDetection()
        except Exception as e:
            messagebox.showerror("Could not arm", f"Sensor setup failed:\n{e}")
            return
        self.stopEvent.clear()
        self.sensorThread = threading.Thread(target=self.runSensorDetection, daemon=True)
        self.sensorThread.start()
        self.armButton.config(text="Disarm System", fg="red")
        self.statusLabel.config(text="System: ARMED (verify again to disarm)", fg="red")
        self.resetVerification()
        print("System Armed: True")

    #Stop polling; the sensor thread turns off the laser and cleans up GPIO when it exits
    def disarm(self):
        self.stopEvent.set()
        self.armButton.config(text="Arm System", fg="green")
        self.statusLabel.config(text="System: Disarmed", fg="black")
        self.resetVerification()
        print("System Armed: False")

    #Run sensor system until disarmed
    def runSensorDetection(self):
        sensors = self.sensors
        try:
            while not self.stopEvent.is_set():
                try:
                    sensors.printSensors()
                except Exception as e:
                    # One bad read or a network hiccup shouldn't stop monitoring
                    print(f"Error during sensor poll: {e}")
                self.stopEvent.wait(config.POLL_INTERVAL_SECONDS)
        finally:
            sensors.terminate()

    # ---------------------------------------------------------------- widgets
    def updateClock(self):
        self.clockLabel.config(text=time.strftime("%H:%M:%S"))
        self.root.after(1000, self.updateClock)

    #Change weather information for GUI, refreshed every 30 minutes
    def updateWeather(self):
        def onDone(text, error):
            if error:
                print(f"Weather error: {error}")
                self.weatherLabel.config(text="Error loading weather information")
            else:
                self.weatherLabel.config(text=text)
        self.runInBackground(lambda: weatherInformation.getWeatherSummary(False), onDone)
        self.root.after(30 * 60 * 1000, self.updateWeather)

    def onClose(self):
        # Closing the window would stop monitoring, so it needs a verified disarm first
        if self.isArmed():
            messagebox.showwarning("System armed", "Verify and disarm the system before closing.")
            return
        if self.sensorThread is not None and self.sensorThread.is_alive():
            self.sensorThread.join(timeout=10)
        self.root.destroy()


def main():
    root = tk.Tk()
    SecurityApp(root)
    #Keep running application
    root.mainloop()


if __name__ == "__main__":
    main()
