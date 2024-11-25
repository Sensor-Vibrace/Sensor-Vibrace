import RPi.GPIO as GPIO
import time
import bluetooth

TRIG = 24
ECHO = 23

GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

# bluetooth setting
server_socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
server_socket.bind(("", bluetooth.PORT_ANY))
server_socket.listen(1)
port = server_socket.getsockname()[1]
print(f"Waiting for Bluetooth connection on port {port}")
client_socket, client_address = server_socket.accept()
print(f"Accepted connection from {client_address}")

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
            print("Object detected within 50 cm!")
            # send message by bluetooth
            message = "Object detected! (Person or Parcel)"
            client_socket.send(message)  

            time.sleep(2)   
        time.sleep(0.1)
except KeyboardInterrupt:
    print("Program terminated by user")
    client_socket.close()
    server_socket.close()
    GPIO.cleanup()