from flask import Flask, Response #use this to send video stream link
import cv2;
import numpy as np
import matplotlib.pyplot as plt
Class response:
  keepRunning=true
  def transmitFeed():
    cap=cv2.VideoCapture(0);
    while keepRunning:#ret is if webcam is available, frame is next frame
        ret, frame = cap.read()
        if not ret:
            break
        # Process the frame here if needed (e.g., add text, apply filters) DO THIS

        cv2.imshow('Live Feed', frame)
        #q to end stream
        if cv2.waitKey(1) == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
  def threatLevel(sensorValues[]):

  def sendAlert():

  def alarmSystem():#picture, buzzer, leds
    
  def voiceReco():

  def toggle():
    keepRunning=!keepRunning

    

  

