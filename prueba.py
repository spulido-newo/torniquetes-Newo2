import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)

PIN = 17  # GPIO17, pin f�sico 11
GPIO.setup(PIN, GPIO.OUT)

try:
    print("Encendiendo el pin...")
    GPIO.output(PIN, GPIO.HIGH)
    time.sleep(5)
    print("Apagando el pin...")
    GPIO.output(PIN, GPIO.LOW)
finally:
    GPIO.cleanup()
    print("Limpieza GPIO completada")