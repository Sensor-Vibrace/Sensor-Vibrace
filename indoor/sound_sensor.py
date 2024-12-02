import spidev
import time

spi = spidev.SpiDev()
spi.open(0, 0)  # bus 0, device 0
spi.max_speed_hz = 1350000

def read_adc(channel):
    if channel < 0 or channel > 7:
        return -1
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    data = ((adc[1] & 3) << 8) + adc[2]
    return data

def analog_to_dB(analog_value, max_value=1023, max_db=100):
    return (analog_value / max_value) * max_db

try:
    while True:
        analog_value = read_adc(0)
        
        dB_value = analog_to_dB(analog_value)
        
        print(f"Analog value: {analog_value}, Sound Level: {dB_value} dB")
        
        time.sleep(0.1)

except KeyboardInterrupt:
    pass
finally:
    spi.close()
    print("Program exited")
