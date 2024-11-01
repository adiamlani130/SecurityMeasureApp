#import necesssary libraries and packages
import RPi.GPIO as GPIO
import time
import Adafruit_DHT
import Response
#sensorDetection class takes values from several sensors
class sensorDetection:
   def __init__(self):
       #Inital Setup
       GPIO.setmode(GPIO.BCM)  # Use Broadcom pin numbering
       #Gas setup
       self.gasPin = 1  # Replace with actual GPIO pin number
       GPIO.setup(self.gasPin, GPIO.IN) # Setup the pin as input
       #Flame setup
       self.flamePin=2 # Replace with actual GPIO pin number
       GPIO.setup(self.flamePin, GPIO.IN)
       #Temperature and humidity setup
       self.tempPin=3 # Replace with actual GPIO pin number
       self.tempSensor = Adafruit_DHT.DHT11
       #Infared setup
       self.infaredPin=4 # Replace with actual GPIO pin number
       GPIO.setup(self.infaredPin, GPIO.IN)
       #Rain Sensor setup
       self.sprinklerPin=5 # Replace with actual GPIO pin number
       GPIO.setup(self.sprinklePin,GPIO.IN)
       #Laser setup and activation
       self.laserPin=6 # Replace with actual GPIO pin number
       GPIO.setup(self.laserPin,GPIO.IN)
       GPIO.output(self.laserPin, GPIO.HIGH)  # Turn the laser on
       print("Laser activated, System online")
  
   #Gas Detection
   def gasDetection(self):
       try:
           # Check the digital output of the MQ2 sensor
           if GPIO.input(self.gasPin):
               print("Gas detected!")
               return True
           else:
               print("No gas detected.")
               return False
       except Exception as e:
           print(f"Error: {e}")
      
   #Flame Detection
   def flameDetection(self):
       if GPIO.input(self.flamePin):
           print("Flame detected!")
           return True
       else:
           print("No Flame detected.")
           return False


   #Temperature and Humidity Sensor
   def tempSensor(self):
       humidity, temperature = Adafruit_DHT.read(self.tempSensor, self.tempPin)    
       if humidity is not None and temperature is not None:
           print(f'Temperature: {temperature:.1f}°C, Humidity: {humidity:.1f}%')
           return temperature, humidity
       else:
           print('Failed to get reading from the DHT11 sensor.')
           return -1,-1


   #Infared Sensor Detection
   def infaredSensor(self):
       if GPIO.input(self.infaredPin):
           print("Motion detected!")
           return True
       else:
           print("No Motion detected.")
           return False


       #Infared Sensor Detection
   def sprinklerSensor(self):
       if GPIO.input(self.sprinklerPin):
           print("sprinkle")
           return True
       else:
           print("No sprinkle")
           return False
      
       #Print sensor values and act accordingly with them
   def printSensors():
       sprinklers=sensorDetection.sprinklerSensor()
       infared=sensorDetection.infaredSensor()
       temp,humd=sensorDetection.tempSensor()
       flame=sensorDetection.flameDetection()
       gas = sensorDetection.gasDetection()
       #Initiate response with sensor values
       sensorValues={sprinklers,infared,temp,humd,flame,gas}
       print("\nSprinkler alarm: {}\nIntruder alarm: {}\nTemperature: {}\nHumidity: {}\nFire alarm: {}\nGas sensor: {}\n".format(sprinklers,infared,temp,humd,flame,gas))
       #Trigger response according to sensor values
       Response.respond(sensorValues)
          
   #End sensor run, terminate readings, turn off laser module
   def terminate(self):
       GPIO.output(self.laserPin,GPIO.LOW)
       print("System offline, laser deactivated")
       GPIO.cleanup()
