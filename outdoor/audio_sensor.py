# 설치해야 하는 라이브러리
# pip3 install SpeechRecognition PyBluez pyttsx3


# 음성 감지 및 변환 코드
import RPi.GPIO as GPIO
import time
import spidev
import bluetooth
import speech_recognition as sr
import pyttsx3

# MCP3008 설정
SPI_BUS = 0
SPI_DEVICE = 0
spi = spidev.SpiDev()
spi.open(SPI_BUS, SPI_DEVICE)
spi.max_speed_hz = 1350000

# 블루투스 설정
server_socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
server_socket.bind(("", bluetooth.PORT_ANY))
server_socket.listen(1)
port = server_socket.getsockname()[1]
print("Waiting for Bluetooth connection on port", port)
client_socket, client_address = server_socket.accept()
print("Accepted connection from", client_address)

# 텍스트 음성 변환 엔진 설정
tts_engine = pyttsx3.init()

def read_adc(channel):
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    data = ((adc[1] & 3) << 8) + adc[2]
    return data

def process_audio():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()  # MAX9814에 연결된 마이크 입력
    try:
        with mic as source:
            print("Listening for external voice...")
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source)
        text = recognizer.recognize_google(audio)
        print(f"Recognized text: {text}")
        client_socket.send(text)  # 블루투스로 텍스트 전송
    except sr.UnknownValueError:
        print("Could not understand audio")
    except sr.RequestError as e:
        print(f"Error with the speech recognition service: {e}")

try:
    while True:
        mic_value = read_adc(0)  # MCP3008의 CH0에서 읽기
        if mic_value > 500:  # 임계값 설정 (필요에 따라 조정)
            process_audio()  # 음성 감지 후 처리
        
        # 블루투스에서 메시지 수신 및 TTS 출력
        received_text = client_socket.recv(1024).decode('utf-8')
        if received_text:
            print(f"Received response: {received_text}")
            tts_engine.say(received_text)
            tts_engine.runAndWait()

except KeyboardInterrupt:
    print("Program terminated by user")
    client_socket.close()
    server_socket.close()
    GPIO.cleanup()
