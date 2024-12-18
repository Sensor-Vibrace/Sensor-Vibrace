import spidev
import time
import math
import os

SOUND_SENSOR_CHANNEL = 4  
AVERAGE_MEASURE_DURATION = 10  
OUTPUT_FILE = "average_sound_level.txt"

spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 500000

def read_adc(channel):
    if channel < 0 or channel > 7:
        return -1
    r = spi.xfer2([1, (8 + channel) << 4, 0])
    adc_out = ((r[1] & 3) << 8) + r[2]
    return adc_out * 1.5

def measure_average_noise(duration):
    print("Measuring average noise level...")
    adc_values = []

    for _ in range(duration * 10):  
        adc_value = read_adc(SOUND_SENSOR_CHANNEL)
        if adc_value > 0:
            adc_values.append(adc_value)
        time.sleep(0.1)
        
    if adc_values:
        avg_adc = sum(adc_values) / len(adc_values)
        avg_db = 20 * math.log10(avg_adc / 1024.0)
        print(f"Measured Average Sound Level: {avg_db:.2f} dB")

        with open(OUTPUT_FILE, "w") as f:
            f.write(f"Average Sound Level: {avg_db:.2f} dB\n")
        print(f"Average sound level saved to {OUTPUT_FILE}")
    else:
        print("Failed to collect ADC readings. No valid data.")

if __name__ == "__main__":
    try:
        measure_average_noise(AVERAGE_MEASURE_DURATION)
    except KeyboardInterrupt:
        print("Program interrupted by user.")
    finally:
        spi.close()
        print("Program terminated.")