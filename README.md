SecurityMeasureApp

SecurityMeasureApp is an IoT-based security and monitoring application designed for deployment on a Raspberry Pi 400. The system integrates environmental sensors, motion detection, computer vision, and AWS cloud services to detect potential threats such as fire, smoke, intrusion, and extreme weather conditions, and to notify users in real time.

Features
Fire and Smoke Detection

MQ-2 Gas Sensor

Flame Sensor

Environmental Monitoring

DHT11 Temperature and Humidity Sensor

Rain Sensor

Weather data integration via the Open-Meteo API

Intrusion Detection

HC-SR501 Infrared Motion Sensor

System Status Indicators

KY-008 Laser Sensor indicating armed/disarmed status

LED indicators displaying individual sensor states

Identity Verification

Facial recognition using AWS Rekognition

Voice authentication using AWS Transcribe

Threat Assessment and Alerts

Sensor data collected every 5 seconds

Built-in linear regression model estimates threat severity and expected cost

Automated threat summaries sent to the user via AWS SNS

Hardware Requirements

Raspberry Pi 400

MQ-2 Gas Sensor

Flame Sensor

DHT11 Temperature and Humidity Sensor

Rain Sensor

HC-SR501 PIR Motion Sensor

KY-008 Laser Sensor

LEDs and resistors

Breadboard and jumper wires

USB or Pi-compatible webcam

Software Dependencies

Install the required Python libraries using pip:

pip install openmeteo-requests
pip install RPi.GPIO
pip install numpy
pip install pandas
pip install requests-cache
pip install retry-requests
pip install Adafruit_DHT
pip install opencv-python
pip install boto3

AWS Requirements

Valid AWS account

Configured AWS credentials on the Raspberry Pi

Read/write access to an S3 bucket for storing images and data

Verified SNS phone number for message delivery

Enabled services:

AWS Rekognition

AWS Transcribe

AWS SNS

Amazon S3

Application Workflow

User identity is verified using AWS Rekognition and AWS Transcribe.

Once armed, the system polls all sensors every 5 seconds.

Sensor readings are passed to the threat assessment algorithm.

The linear regression model evaluates threat severity and estimated cost.

A summary alert is sent to the user via AWS SNS.

Weather data from the Open-Meteo API is included in the dashboard and alert messages.

Setup Notes

Ensure all GPIO pin connections match the pin configuration defined in the code.

Confirm reliable circuit connections between the Raspberry Pi, sensors, and LEDs.

A functional webcam must be connected to the Raspberry Pi prior to running the application.

Network connectivity is required for AWS and weather API access.

Disclaimer

This project is intended for educational and demonstration purposes. It is not designed for use as a certified safety or security system.
