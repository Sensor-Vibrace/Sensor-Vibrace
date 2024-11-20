import RPi.GPIO as GPIO
import time

SENSOR_PIN = 18  

GPIO.setmode(GPIO.BCM)
GPIO.setup(SENSOR_PIN, GPIO.IN)

try:
    while True:
        if GPIO.input(SENSOR_PIN):  
            print("Vibration detected!") 
        else:
            print("No vibration detected.")  
        time.sleep(0.1)  
except KeyboardInterrupt:
    GPIO.cleanup()  