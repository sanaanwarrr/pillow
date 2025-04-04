import time
import numpy as np
from hx711 import HX711
import RPi.GPIO as GPIO

DT_PIN = 17
SCK_PIN = 27

hx = HX711(dout_pin=DT_PIN, pd_sck_pin=SCK_PIN)
hx.set_reading_format("MSB", "MSB")

print("Taring the sensor... Remove any weight.")
hx.reset()
hx.tare()
print("Tare complete. Place a known weight on the sensor.")

time.sleep(2)

def calibrate(weight_on_sensor):
    print("Place a known weight on the sensor.)")
    time.sleep(5)  

    readings = [hx.get_weight(5) for _ in range(10)]
    average_reading = np.mean(readings)
    
    scale_ratio = average_reading / weight_on_sensor
    print(f"Calibration Complete. Scale Ratio: {scale_ratio}")
    
    return scale_ratio

if __name__ == "__main__":
    try:
        known_weight = float(input("Enter the known weight in grams (e.g., 1000 for 1kg): "))
        scale_ratio = calibrate(known_weight)
        print(f"Use this scale ratio in your code: {scale_ratio}")
    except KeyboardInterrupt:
        print("Calibration interrupted.")
    finally:
        GPIO.cleanup()
