import RPi.GPIO as GPIO
import time
import spidev

SPI_BUS = 0
SPI_DEVICE = 0
spi = spidev.SpiDev()
spi.open(SPI_BUS, SPI_DEVICE)
spi.max_speed_hz = 1350000

GPIO.setmode(GPIO.BCM)

def read_adc(channel):
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    data = ((adc[1] & 3) << 8) + adc[2]
    return data

try:
    while True:
        mic_value = read_adc(0)
        print(f"Sensor Value: {mic_value}")
        time.sleep(0.1)
except KeyboardInterrupt:
    GPIO.cleanup()