# SecurityMeasureApp
# The Security Measure App is an application linked to a RASBERRY PI 400 Unit. It utilizes an MQ-2 gas sensor as well as a flame sensor to detect possible fires and smoke. 
# The Pi is also paired with a rain sensor and DHT11 temperature sensor in case of harsh weather conditions in the place of deployment.
# A HC-SR501 infared human sensor.
# A KY-008 Laser sensor indicates that on/off status of the app.
# The sensors are paired with LEDs,that indicate the status of the sensors.
# Dependencies:
# The app needs the following python libraries, run the commands below to install them.
# pip install openmeteo-requests
# pip install RPi.GPIO
# pip install numpy
# pip install pandas
# pip install requests-cache
# pip install retry-requests
# pip install Adafruit_DHT
# pip install cv2
# pip install boto3
# Ensure that the pi unit has a functional webcam connection.
# This app uses a few aws services. A valid aws account would be needed to use the required services.
# Must have read/write access to an s3 bucket, local file system to store images etc,
# and a sandbox verified phone number for sns
# AWS credentials would need to be configured into the app.


# Ensure GPIO pin connection between Raspberry Pi, breadboard, sensors, LEDS aligns with pins used in code, ensure circuit is reliable
# To begin application, user must verify identity through AWS face rekognition and AWS transcribe
# When armed, sensors will register values every 5 seconds and send to threat algorithm
# The linear regression algorithm built in the app will assess expected cost, estimate threat level and send corresponding summary via SNS to user
# openmeteo free API used to display location data on the homepage and in the SNS message sent to the user.
