# RPi.GPIO 라이브러리 설치 코드 (필요 시)
# sudo apt-get update
# sudo apt-get install python3-rpi.gpio

# PyBluez 라이브러리 설치 코드
# sudo apt-get install python3-pybluez


import RPi.GPIO as GPIO
import time
import bluetooth  # PyBluez를 사용한 블루투스 모듈 추가

# 핀 설정
TRIG = 17  # Trig 핀 연결 (라즈베리파이의 GPIO 핀 번호)
ECHO = 27  # Echo 핀 연결 (라즈베리파이의 GPIO 핀 번호)

# GPIO 모드 설정
GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

# 블루투스 설정
server_socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
server_socket.bind(("", bluetooth.PORT_ANY))
server_socket.listen(1)
port = server_socket.getsockname()[1]
print("Waiting for Bluetooth connection on port", port)

# 클라이언트(스마트폰) 연결 대기
client_socket, client_address = server_socket.accept()
print("Accepted connection from", client_address)

def measure_distance():
    # Trig 핀을 짧게 High로 설정하여 초음파 발사
    GPIO.output(TRIG, True)
    time.sleep(0.00001)  # 10µs 동안 신호 발생
    GPIO.output(TRIG, False)

    # Echo 핀이 신호를 수신할 때까지 대기
    while GPIO.input(ECHO) == 0:
        start_time = time.time()

    while GPIO.input(ECHO) == 1:
        end_time = time.time()

    # 초음파가 이동한 시간 계산
    elapsed_time = end_time - start_time
    distance = (elapsed_time * 34300) / 2  # cm로 변환 (왕복 거리이므로 /2)
    return distance

try:
    while True:
        distance = measure_distance()
        print(f"Measured Distance: {distance:.2f} cm")
        
        # 특정 거리 내에 물체 감지 시 경고 출력 및 블루투스 메시지 전송
        if distance < 50:  # 예: 50cm 이내에 물체 감지
            print("Object detected! (Person or Parcel)")
            message = "Object detected at {:.2f} cm!".format(distance)
            client_socket.send(message)  # 블루투스를 통해 메시지 전송
        
        time.sleep(1)  # 1초 대기
except KeyboardInterrupt:
    print("Measurement stopped by User")
    client_socket.close()
    server_socket.close()
    GPIO.cleanup()