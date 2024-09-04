# SecurityMeasureApp
# The Security Measure App is an application linked to a RASBERRY PI 400 Unit. It utilizes an MQ-2 gas sensor as well as a flame sensor to detect possible fires and smoke.  
# The Pi is also paired with a rain sensor and DHT11 temperature sensor in case of harsh weather conditions in the place of deployment.
# A wireless transmitter and reciever is also used to pass signals that arm or disarm the system. 
# A shock sensor paired with a HC-SR501 human infared sensor detects the breaking of glass or a door and the presence of humans.
# A KY-008 Laser sensor indicates that on/off status of the app and a sound sensor that can detect sudden loud noises.
# The sensors are paired with LEDs, buzzers, and buttons that can indicate the status of the sensors. To accompany these alerts, a webcam also captures a picture of the room.
# In addition to many complex functions testing and recording each sensor's data, an AWS program sends an alert to the owner of whatever sensors have been triggered.
# The application also uses a linear regression algorithm to categorize each threat and label it with what possible issues could be the source.
