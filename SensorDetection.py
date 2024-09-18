import RPi.GPIO as GPIO
import time
import Adafruit_DHT
class SensorDetection:
  def__init__(self):
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
        else:
            print("No gas detected.")
    except Exception as e:
        print(f"Error: {e}")
      
  #Flame Detection
  def flameDetection(self):
      if GPIO.input(self.flamePin):
            print("Flame detected!")
        else:
            print("No Flame detected.")
    except Exception as e:
        print(f"Error: {e}")

  #Temperature and Humidity Sensor
  def tempSensor(self):
    humidity, temperature = Adafruit_DHT.read(self.tempSensor, self.tempPin)     
    if humidity is not None and temperature is not None:
        print(f'Temperature: {temperature:.1f}°C, Humidity: {humidity:.1f}%')
    else:
        print('Failed to get reading from the DHT11 sensor.')

    #Infared Sensor Detection
    def infaredSensor(self):
      if GPIO.input(self.infaredPin):
            print("Motion detected!")
        else:
            print("No Motion detected.")
    except Exception as e:
        print(f"Error: {e}")

    #Infared Sensor Detection
    def sprinklerSensor(self):
      if GPIO.input(self.sprinklerPin):
            print("Sprinkler going off!")
        else:
            print("No Sprinkler detected.")
    except Exception as e:
        print(f"Error: {e}")


  def terminate(self):
    Gpio.output(self.laserPin,GPIO.LOW)
    print("System offline, laser deactivated")
    GPIO.cleanup()
