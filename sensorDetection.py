#import necessary libraries and packages
import time
import RPi.GPIO as GPIO
import board
import adafruit_dht
import config
import response


#sensorDetection class takes values from several sensors
class sensorDetection:
    def __init__(self):
        #Inital Setup
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)  # Use Broadcom (GPIOxx) pin numbering
        #Digital input sensors: gas, flame, motion (infrared), rain
        self.gasPin = config.GAS_PIN
        self.flamePin = config.FLAME_PIN
        self.infraredPin = config.MOTION_PIN
        self.rainPin = config.RAIN_PIN
        for pin in (self.gasPin, self.flamePin, self.infraredPin, self.rainPin):
            GPIO.setup(pin, GPIO.IN)
        #Temperature and humidity setup (DHT11 via the CircuitPython driver, which supports the Pi 4/400)
        self.dhtSensor = adafruit_dht.DHT11(getattr(board, f"D{config.DHT_PIN}"))
        #Optional per-sensor status LEDs (-1 = not connected)
        self.ledPins = {
            "gas": config.GAS_LED_PIN,
            "flame": config.FLAME_LED_PIN,
            "intruder": config.MOTION_LED_PIN,
            "rain": config.RAIN_LED_PIN,
        }
        for pin in self.ledPins.values():
            if pin >= 0:
                GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)
        #Laser setup and activation (laser on = system armed)
        self.laserPin = config.LASER_PIN
        GPIO.setup(self.laserPin, GPIO.OUT, initial=GPIO.HIGH)
        print("Laser activated, System online")

    #Read a digital sensor, accounting for modules whose output goes LOW on detection
    @staticmethod
    def _triggered(pin, activeLow):
        level = GPIO.input(pin)
        return (level == GPIO.LOW) if activeLow else (level == GPIO.HIGH)

    #Gas Detection
    def gasDetection(self):
        detected = self._triggered(self.gasPin, config.GAS_ACTIVE_LOW)
        print("Gas detected!" if detected else "No gas detected.")
        return detected

    #Flame Detection
    def flameDetection(self):
        detected = self._triggered(self.flamePin, config.FLAME_ACTIVE_LOW)
        print("Flame detected!" if detected else "No flame detected.")
        return detected

    #Temperature and Humidity Sensor, returns (celsius, humidity) or (None, None) if the read failed
    def readTemperature(self, attempts=3):
        for _ in range(attempts):
            try:
                temperature = self.dhtSensor.temperature
                humidity = self.dhtSensor.humidity
                if temperature is not None and humidity is not None:
                    print(f'Temperature: {temperature:.1f}°C, Humidity: {humidity:.1f}%')
                    return temperature, humidity
            except RuntimeError as e:
                # DHT sensors frequently miss a read; just try again
                print(f"DHT11 read error: {e}")
            time.sleep(2)  # DHT11 needs ~1-2s between reads
        print('Failed to get reading from the DHT11 sensor.')
        return None, None

    #Infrared (PIR) Motion Detection
    def infraredSensor(self):
        detected = self._triggered(self.infraredPin, config.MOTION_ACTIVE_LOW)
        print("Motion detected!" if detected else "No motion detected.")
        return detected

    #Rain Sensor Detection
    def rainSensor(self):
        detected = self._triggered(self.rainPin, config.RAIN_ACTIVE_LOW)
        print("Rain/water detected!" if detected else "No rain/water detected.")
        return detected

    #Light the LED for each sensor that is currently triggered
    def updateLeds(self, sensorValues):
        for name, pin in self.ledPins.items():
            if pin >= 0:
                GPIO.output(pin, GPIO.HIGH if sensorValues[name] else GPIO.LOW)

    #Read every sensor once and return the values
    def readSensors(self):
        temp, humd = self.readTemperature()
        return {
            "rain": self.rainSensor(),
            "intruder": self.infraredSensor(),
            "temperature": temp,
            "humidity": humd,
            "flame": self.flameDetection(),
            "gas": self.gasDetection(),
        }

    #Print sensor values and act accordingly with them
    def printSensors(self):
        sensorValues = self.readSensors()
        print("\nRain alarm: {rain}\nIntruder alarm: {intruder}\nTemperature: {temperature}\n"
              "Humidity: {humidity}\nFire alarm: {flame}\nGas sensor: {gas}\n".format(**sensorValues))
        self.updateLeds(sensorValues)
        #Trigger response according to sensor values
        response.respond(sensorValues)
        return sensorValues

    #End sensor run, terminate readings, turn off laser module
    def terminate(self):
        try:
            GPIO.output(self.laserPin, GPIO.LOW)
            self.dhtSensor.exit()
        finally:
            GPIO.cleanup()
        print("System offline, laser deactivated")
