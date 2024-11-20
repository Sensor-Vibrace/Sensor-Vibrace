# RPi.GPIO 라이브러리 설치 코드 (필요 시)
# sudo apt-get update
# sudo apt-get install python3-rpi.gpio

# PyBluez 라이브러리 설치 코드
# sudo apt-get install python3-pybluez


import RPi.GPIO as GPIO
import time
import bluetooth  # PyBluez를 사용한 블루투스 모듈

# 진동 감지 센서 설정
SENSOR_PIN = 18  # SW-420의 DO 핀 연결 (라즈베리파이의 GPIO 핀)

# GPIO 설정
GPIO.setmode(GPIO.BCM)
GPIO.setup(SENSOR_PIN, GPIO.IN)

# 블루투스 설정
server_socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
server_socket.bind(("", bluetooth.PORT_ANY))
server_socket.listen(1)
port = server_socket.getsockname()[1]
print("Waiting for Bluetooth connection on port", port)

# 클라이언트(스마트폰) 연결 대기
client_socket, client_address = server_socket.accept()
print("Accepted connection from", client_address)

try:
    print("Monitoring for vibrations...")
    while True:
        if GPIO.input(SENSOR_PIN):  # 진동 감지 시
            print("Vibration detected! (Knock or impact)")
            message = "Vibration detected at the door! (Knock or Impact)"
            client_socket.send(message)  # 블루투스 알림 전송
            
            # 감지 후 일정 시간 대기 (노이즈 방지용)
            time.sleep(2)
        time.sleep(0.1)  # 감지 주기
except KeyboardInterrupt:
    print("Program terminated by user")
    client_socket.close()
    server_socket.close()
    GPIO.cleanup()
