import RPi.GPIO as GPIO
import time

TRIG = 24
ECHO = 23

GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

def measure_distance():
    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)

    while GPIO.input(ECHO) == 0:
        start_time = time.time()

    while GPIO.input(ECHO) == 1:
        end_time = time.time()

    elapsed_time = end_time - start_time
    distance = (elapsed_time * 34300) / 2
    return distance

try:
    while True:
        distance = measure_distance()
        print(f"Measured Distance: {distance:.2f} cm")
        
        if distance < 50:
            print("Object detected! (Person or Parcel)")
        
        time.sleep(1)
except KeyboardInterrupt:
    print("Measurement stopped by User")
    GPIO.cleanup()