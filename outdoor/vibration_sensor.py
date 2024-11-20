import RPi.GPIO as GPIO
import time

SENSOR_PIN = 18  # SW-420의 DO 핀 연결

GPIO.setmode(GPIO.BCM)
GPIO.setup(SENSOR_PIN, GPIO.IN)

try:
    while True:
        if GPIO.input(SENSOR_PIN):  # 진동 감지
            print("Vibration detected!")  # 진동 감지 시 메시지 출력
        else:
            print("No vibration detected.")  # 진동 미감지 시 메시지 출력
        time.sleep(0.1)  # 짧은 주기로 상태 확인
except KeyboardInterrupt:
    GPIO.cleanup()  # 프로그램 종료 시 GPIO 핀 정리