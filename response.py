#import necessary libraries and packages
import os
import time
import pandas as pd
from sklearn.linear_model import LinearRegression
import config
import sendMessage

_verifier = None
_costModel = None
_lastAlertTime = None

FEATURES = ['Rain', 'Infrared', 'Temperature', 'Humidity', 'Flame', 'Gas']


#AWS clients are created on first use so importing this module needs no AWS setup
def _getVerifier():
    global _verifier
    if _verifier is None:
        from verification import Verification
        _verifier = Verification()
    return _verifier


#Calculate urgency of situation
def calcThreatLevel(sensorValues):
    #Simple algorithm to add urgency to assess situation
    urgency = 0
    temperature = sensorValues["temperature"]
    humidity = sensorValues["humidity"]
    # A failed DHT11 read gives None; don't treat that as an emergency
    if temperature is not None and (temperature > config.TEMP_HIGH_C or temperature < config.TEMP_LOW_C):
        urgency += 1
    if humidity is not None and humidity > config.HUMIDITY_HIGH:
        urgency += 1
    if sensorValues["gas"]:
        urgency += 3  # Gas detection significantly increases urgency
    if sensorValues["flame"]:
        urgency += 3  # Fire detection is highly critical
    if sensorValues["intruder"]:
        urgency += 3  # Intruder detection is highly critical
    if sensorValues["rain"]:
        urgency += 1  # Water detected (rain / leak / sprinklers)
    return urgency


#Linear Regression model to assess expected financial loss (trained once, on first use)
def _getCostModel():
    global _costModel
    if _costModel is None:
        #Data for predicted financial loss (temperatures in °F)
        data = {
            'Rain': [1, 0, 1, 0, 1, 0, 1, 1, 0, 1],
            'Infrared': [0, 1, 0, 1, 0, 1, 1, 0, 1, 0],
            'Temperature': [85, 100, 70, 95, 90, 75, 60, 50, 40, 30],
            'Humidity': [50, 20, 60, 10, 45, 30, 25, 70, 55, 20],
            'Flame': [0, 1, 0, 1, 0, 1, 0, 1, 0, 0],
            'Gas': [0, 1, 0, 1, 1, 0, 0, 1, 0, 1],
            'Financial Loss': [500, 30000, 200, 15000, 1000, 2500, 50, 40000, 1000, 0]}
        df = pd.DataFrame(data)
        model = LinearRegression()
        model.fit(df[FEATURES], df['Financial Loss'])
        _costModel = model
    return _costModel


def expectedCost(sensorValues):
    model = _getCostModel()
    temperatureC = sensorValues["temperature"]
    # The model was trained in °F; fall back to a typical room temperature if the DHT11 read failed
    temperatureF = temperatureC * 9 / 5 + 32 if temperatureC is not None else 70
    humidity = sensorValues["humidity"] if sensorValues["humidity"] is not None else 40
    row = pd.DataFrame([[
        int(bool(sensorValues["rain"])),
        int(bool(sensorValues["intruder"])),
        temperatureF,
        humidity,
        int(bool(sensorValues["flame"])),
        int(bool(sensorValues["gas"])),
    ]], columns=FEATURES)
    predictedLoss = max(0.0, float(model.predict(row)[0]))  # a negative loss makes no sense
    return f"Predicted financial loss: ${predictedLoss:,.2f}\n"


#Create message summarizing sensor values and threat level
def createMessage(values, url, level):
    #Insert all sensor values into message
    message = "\nSensor Summary:\n"
    message += "Rain/water alarm: {}\n".format("Activated" if values["rain"] else "Not activated")
    message += "Intruder alarm: {}\n".format("Detected" if values["intruder"] else "No detection")
    message += "Temperature: {}\n".format(f"{values['temperature']}°C" if values["temperature"] is not None else "unavailable")
    message += "Humidity: {}\n".format(f"{values['humidity']}%" if values["humidity"] is not None else "unavailable")
    message += "Fire alarm: {}\n".format("Detected" if values["flame"] else "No detection")
    message += "Gas sensor: {}\n".format("Detected" if values["gas"] else "No detection")
    if url:
        message += "Video of security feed: {}\n".format(url)
    # Add urgency level to the message
    if level > 5:
        message += "\nUrgency Level: HIGH\nImmediate action required!\n"
    elif level > 2:
        message += "\nUrgency Level: MEDIUM\nMonitor the situation.\n"
    else:
        message += "\nUrgency Level: LOW\nSituation minimal\n"
    #Add expected cost to message
    message += expectedCost(values)
    return message


#Take a short video of room and upload it, returns a temporary link (or None if it failed)
def alarmSystem():
    if not config.S3_BUCKET:
        print("S3_BUCKET is not set; skipping security video")
        return None
    verifier = _getVerifier()
    fileName = time.strftime("securityFeed-%Y%m%d-%H%M%S.mp4")
    try:
        verifier.captureVideo(fileName, config.ALARM_VIDEO_SECONDS)
        objectName = verifier.uploadToS3(fileName, config.S3_BUCKET, f"alarms/{fileName}")
        return verifier.presignedUrl(config.S3_BUCKET, objectName)
    except Exception as e:
        print(f"Could not record/upload security video: {e}")
        return None
    finally:
        if os.path.exists(fileName):
            os.remove(fileName)


#Respond to possible dangers/threats
def respond(sensorValues):
    global _lastAlertTime
    level = calcThreatLevel(sensorValues)
    #Only send alert if a sensor goes off, and not more often than the cooldown allows
    if level < 1:
        return False
    now = time.monotonic()
    if _lastAlertTime is not None and now - _lastAlertTime < config.ALERT_COOLDOWN_SECONDS:
        print(f"Threat level {level}, alert already sent recently - waiting for cooldown")
        return False
    _lastAlertTime = now
    url = alarmSystem()
    message = createMessage(sensorValues, url, level)
    print(message)
    sendMessage.send_sms(config.ALERT_PHONE_NUMBER, message)
    return True
