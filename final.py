import RPi.GPIO as GPIO
import time
import serial
import spidev
import math
import speech_recognition as sr
import os
import subprocess
from datetime import datetime
import unicodedata
from gtts import gTTS

# Pin and Port Configuration
TRIG = 24
ECHO = 23
VIBRATION_PIN = 18
SOUND_SENSOR_CHANNEL = 4
MAGNET_SENSOR_PIN = 21
BLUETOOTH_PORT = "/dev/serial0"
BAUD_RATE = 9600
MIC_RECORD_SECONDS = 3
AUDIO_SAVE_DIR = "./recordings"
RECEIVED_RESPONSE_FILE = "./response.mp3"

VIBRATION_THRESHOLD = 0.1
SOUND_THRESHOLD_OFFSET = 4

# GPIO Setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)
GPIO.setup(VIBRATION_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(MAGNET_SENSOR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Bluetooth Setup
bluetooth = serial.Serial(BLUETOOTH_PORT, baudrate=BAUD_RATE, timeout=1)

# SPI for Sound Sensor
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 500000

# Filename Sanitization Function
def sanitize_filename(filename):
    return ''.join(
        c if unicodedata.category(c) != 'Mn' else ''
        for c in unicodedata.normalize('NFD', filename)
        if ord(c) < 128
    ).replace(' ', '_')

# Generate New Filename with Timestamp
def generate_audio_filename():
    os.makedirs(AUDIO_SAVE_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return os.path.join(AUDIO_SAVE_DIR, f"voice_{timestamp}.wav")
    
# Text-to-Speech and Speaker Output
def tts_and_play(text):
    try:
        print("Converting text to speech...")
        tts = gTTS(text=text, lang="ko")
        tts.save(RECEIVED_RESPONSE_FILE)
        print("Playing the response through the speaker...")
        subprocess.run(["mpg123", RECEIVED_RESPONSE_FILE])
    except Exception as e:
        print(f"Failed to process TTS: {e}")

# Sound Level
def read_average_sound_level():
    try:
        with open("average_sound_level.txt", "r") as avg_file:
            line = avg_file.readline()
            return float(line.split(":")[1].strip().split()[0])
    except FileNotFoundError:
        print("Average sound level file not found.")
        return None

def read_adc(channel):
    if channel < 0 or channel > 7:
        return -1
    r = spi.xfer2([1, (8 + channel) << 4, 0])
    adc_out = ((r[1] & 3) << 8) + r[2]
    return adc_out * 1.5

# Distance Measurement
def measure_distance():
    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)

    pulse_start = time.time()
    while GPIO.input(ECHO) == 0:
        pulse_start = time.time()
    while GPIO.input(ECHO) == 1:
        pulse_end = time.time()

    pulse_duration = pulse_end - pulse_start
    return round(pulse_duration * 17150, 2)
    
# Bluetooth Message
def send_bluetooth_message(message):
    try:
        encoded_message = message.encode("utf-8")
        bluetooth.write(encoded_message + b'\n')
        print(f"Bluetooth Message Sent: {encoded_message.decode('utf-8')}\n")
    except Exception as e:
        print(f"Bluetooth Transmission Error: {e}\n")
        
# Bluetooth Message Reception
def receive_bluetooth_message():
    try:
        if bluetooth.in_waiting > 0:
            response = bluetooth.readline().decode("utf-8").strip()
            print(f"Bluetooth Message Received: {response}")
            return response
    except Exception as e:
        print(f"Bluetooth Reception Error: {e}")
    return None

# Vibration Detection
def detect_vibration():
    start_time = time.time()
    while time.time() - start_time < VIBRATION_THRESHOLD:
        if GPIO.input(VIBRATION_PIN) == GPIO.HIGH:
            print("Vibration detected! Sending Bluetooth alert...\n")
            send_bluetooth_message("Knock detected at the door.")
            time.sleep(2)
            break

# Noise Detection
def detect_noise(average_db):
    sound_level_adc = read_adc(SOUND_SENSOR_CHANNEL)
    if sound_level_adc > 0:
        sound_level_db = 20 * math.log10(sound_level_adc / 1024.0)
        relative_sound_level = max(sound_level_db - average_db, 0)
    else:
        relative_sound_level = 0

    print(f"Relative Sound Level: {relative_sound_level:.2f} dB\n")
    if relative_sound_level >= SOUND_THRESHOLD_OFFSET:
        print("High noise level detected! Sending Bluetooth alert...\n")
        send_bluetooth_message("Unusual noise detected inside the house.")
        time.sleep(2)

# Door Open Detection
def detect_door_open():
    if GPIO.input(MAGNET_SENSOR_PIN) == GPIO.LOW:
        print("Door opened! Sending Bluetooth alert...\n")
        send_bluetooth_message("The door has been opened.")
        time.sleep(2)

# Record Audio with Tablet
def record_with_tablet():
    print("Recording voice via tablet...\n")
    try:
        filename = generate_audio_filename()

        subprocess.run(["adb", "shell", "am", "start", "-n",
                        "com.coffeebeanventures.easyvoicerecorder/com.digipom.easyvoicerecorder.ui.activity.EasyVoiceRecorderActivity"])
        time.sleep(2)

        subprocess.run(["adb", "shell", "input", "tap", "500", "1500"])  
        time.sleep(1)

        subprocess.run(["adb", "shell", "input", "tap", "586", "1707"])
        print("Recording started...")
        time.sleep(MIC_RECORD_SECONDS)

        subprocess.run(["adb", "shell", "input", "tap", "586", "1707"])
        print("Recording stopped.")
        time.sleep(2)

        subprocess.run(["adb", "shell", "am", "force-stop", "com.coffeebeanventures.easyvoicerecorder"])
        print("Recording app closed.")

        result = subprocess.run(["adb", "shell", "ls", "-t", "/sdcard/Audio/"],
                                capture_output=True, text=True)
        files = result.stdout.splitlines()

        if not files:
            print("No recordings found.\n")
            return None

        latest_file = files[0]
        print(f"Latest file: {latest_file}\n")

        base_filename = sanitize_filename(latest_file.split('.')[0])
        sanitized_filename = f"{base_filename}.wav"
        full_local_path = os.path.join(AUDIO_SAVE_DIR, sanitized_filename)

        remote_path = f"/sdcard/Audio/{latest_file}"
        subprocess.run(["adb", "pull", remote_path, full_local_path])
        print(f"Voice recording pulled successfully as {full_local_path}\n")
        return full_local_path

    except Exception as e:
        print(f"Tablet recording failed: {e}\n")
        return None

# Recognize Voice
def recognize_voice(audio_file):
    recognizer = sr.Recognizer()
    if not os.path.exists(audio_file):
        print("Voice file not found.\n")
        return
    try:
        with sr.AudioFile(audio_file) as source:
            print("Processing audio for speech recognition...\n")
            audio_data = recognizer.record(source)
        recognized_text = recognizer.recognize_google(audio_data, language="ko-KR")
        print(f"Recognized Text: {recognized_text}\n")
        send_bluetooth_message(f"Voice Message: {recognized_text}")
    except sr.UnknownValueError:
        print("Could not understand the audio.\n")
    except sr.RequestError as e:
        print(f"Google Speech Recognition service error: {e}\n")

# Main Function
def main():
    print("Starting Integrated Detection System...\n")
    average_db = read_average_sound_level()
    if average_db is None:
        raise SystemExit("Exiting program due to missing average sound level.\n")
        
    last_detection_time = 0

    try:
        while True:
			# Wait for incoming messages via Bluetooth
            response = receive_bluetooth_message()
            if response:
                print("Processing received Bluetooth message...\n")
                tts_and_play(response)  # Convert text to speech and play
                
            current_time = time.time()  
            
            if current_time - last_detection_time > 60:  
                distance = measure_distance()
                if distance < 50:
                    print(f"Object detected at {distance} cm. Waiting 1 minute before next detection...")
                    send_bluetooth_message(f"Object detected {distance}cm near the door.")
                    last_detection_time = current_time  
                    audio_file = record_with_tablet()
                    if audio_file:
                        recognize_voice(audio_file)
                    time.sleep(2)  

            detect_vibration()
            detect_noise(average_db)
            detect_door_open()
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("Program stopped by user.\n")
    finally:
        GPIO.cleanup()
        bluetooth.close()
        spi.close()
        print("Program terminated.\n")

if __name__ == "__main__":
    main()