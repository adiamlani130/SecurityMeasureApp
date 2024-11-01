#import necessary libraries and packages
import cv2
from securityCode.verification import Verification
import securityCode.sendMessage as sendMessage
#install statements in README.md
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
#Calculate urgency of situation
def calcThreatLevel(sensorValues):
    #Simple algorithm to add urgency to assess situation
    urgency=0
    if sensorValues[2]>90 or sensorValues[2]<40:
        urgency+=1
    if sensorValues[3]>70:
        urgency+=1
    if sensorValues[5]:
        urgency += 3  # Gas detection significantly increases urgency
    if sensorValues[4]:
        urgency += 3  # Fire detection is highly critical
    if sensorValues[1]:
        urgency += 3  # Intruder detection is highly critical
    if sensorValues[0]:
        urgency += 1  # Sprinklers on indicate a fire emergency
    
    return urgency

#Create message summarizing sensor values and threat level
def createMessage(values,url,num):
    #Insert all sensor values into message
    message = "\nSensor Summary:\n"
    message += "Sprinkler alarm: {}\n".format("Activated" if values[0] else "Not activated")
    message += "Intruder alarm: {}\n".format("Detected" if values[1] else "No detection")
    message += "Temperature: {}°C\n".format(values[2])
    message += "Humidity: {}%\n".format(values[3])
    message += "Fire alarm: {}\n".format("Detected" if values[4] else "No detection")
    message += "Gas sensor: {}\n".format("Detected" if values[5] else "No detection")
    message += "Video Link to 5 second security feed: {}\n ".format(url)
    # Add urgency level to the message
    magnitude=num
    if magnitude > 5:
        message += "\nUrgency Level: HIGH\nImmediate action required!\n"
    elif magnitude>2:
        message += "\nUrgency Level: MEDIUM\nMonitor the situation.\n"
    else:
        message += "\nUrgency Level: LOW\nSituation minimal\n"
    #Add expected cost to message
    message+=sendMessage.expectedCost()
    sendMessage.send_sms(123,message)
    print(message)

#Take a 5 second video of room, save the video for user to see
def alarmSystem():
    #Must have set up S3 Bucket and video webcam for mp4
    Verification.captureVideo('securityFeed.mp4',5)
    bucket='securityFeedS3Bucket'
    videoURL = Verification.uploadToS3('securityFeed.mp4','securityFeedS3Bucket')
    return videoURL

#Respond  to possible dangers/threats
def respond(sensorValues):
    level=calcThreatLevel(sensorValues)
    #Only send alert if sensor goes off
    if level>=1:
        url=alarmSystem()
        sendMessage.sendMessage(sensorValues,url,level)

#Linear Regression model to assess expected financial loss
def expectedCost(sensorValues):
    #Data for predicted financial loss
    data = {
    'Sprinklers': [1, 0, 1, 0, 1, 0, 1, 1, 0, 1],
    'Infrared': [0, 1, 0, 1, 0, 1, 1, 0, 1, 0],
    'Temperature': [85, 100, 70, 95, 90, 75, 60, 50, 40, 30],
    'Humidity': [50, 20, 60, 10, 45, 30, 25, 70, 55, 20],
    'Flame': [0, 1, 0, 1, 0, 1, 0, 1, 0, 0],
    'Gas': [0, 1, 0, 1, 1, 0, 0, 1, 0, 1],
    'Financial Loss': [500, 30000, 200, 15000, 1000, 2500, 50, 40000, 1000, 0]}
    # Convert to DataFrame
    df = pd.DataFrame(data)
    # Define features and target variable
    X = df[['Sprinklers', 'Infrared', 'Temperature', 'Humidity', 'Flame', 'Gas']]
    y = df['Financial Loss']
    # Train the model
    model = LinearRegression()
    model.fit(X, y)
    # Model coefficients
    print("Model Coefficients:")
    for feature, coef in zip(X.columns, model.coef_):
        print(f"{feature}: {coef}")
    # Example input for prediction (modify these values as needed)
    predicted_loss = model.predict(sensorValues)
    cost=(f"Predicted Financial Loss for sensors {sensorValues}: ${predicted_loss[0]:,.2f}")
    print(cost)
    return cost