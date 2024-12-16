from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import RPi.GPIO as GPIO
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

app = FastAPI()

# CORS Configuration
origins = [
    "http://localhost",
    "http://localhost:4000",
    "http://127.0.0.1:4000",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GPIO setup
INPUT_PIN = 7
OUTPUT_PIN = 11

GPIO.setmode(GPIO.BCM)  # Use BCM pin numbering
GPIO.setup(INPUT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)  # Pin 7 as input
GPIO.setup(OUTPUT_PIN, GPIO.OUT)  # Pin 11 as output

@app.get("/encender/{pin}")
def encender(pin: int):
    print(f"Pin que esta ingresando de torniquete: {pin}")
    try:
        if pin == OUTPUT_PIN:
            GPIO.output(pin, GPIO.HIGH)
            logging.info(f"Pin {pin} turned on")
            return {"pin": pin, "estado": "encendido"}
        elif pin == 7:  # Cambiado de INPUT_PIN a 7
            GPIO.setup(pin, GPIO.OUT)  # Configura el pin como salida
            GPIO.output(pin, GPIO.HIGH)
            logging.info(f"Pin {pin} turned on")
            return {"pin": pin, "estado": "encendido"}
        else:
            logging.error(f"Pin {pin} is not configured as output")
            return {"error": "Invalid pin for output"}
    except Exception as e:
        logging.error(f"Error turning on pin {pin}: {e}")
        return {"error": str(e)}

@app.get("/apagar/{pin}")
def apagar(pin: int):
    try:
        if pin == OUTPUT_PIN:
            GPIO.output(pin, GPIO.LOW)
            logging.info(f"Pin {pin} turned off")
            return {"pin": pin, "estado": "apagado"}
        elif pin == 7:  # Cambiado de INPUT_PIN a 7
            GPIO.setup(pin, GPIO.OUT)  # Configura el pin como salida
            GPIO.output(pin, GPIO.LOW)
            logging.info(f"Pin {pin} turned off")
            return {"pin": pin, "estado": "apagado"}
        else:
            logging.error(f"Pin {pin} is not configured as output")
            return {"error": "Invalid pin for output"}
    except Exception as e:
        logging.error(f"Error turning off pin {pin}: {e}")
        return {"error": str(e)}

@app.get("/consultar/{pin}")
def consultar(pin: int):
    try:
        if pin == INPUT_PIN:
            estado = GPIO.input(pin)
            estado_str = "alto" if estado == GPIO.HIGH else "bajo"
            logging.info(f"Pin {pin} status: {estado_str}")
            print(f"Pin {pin} status: {estado_str}")

            return {"pin": pin, "estado": estado_str}
        elif pin == OUTPUT_PIN:
            estado = GPIO.input(pin)
            estado_str = "encendido" if estado == GPIO.HIGH else "apagado"
            print(f"Pin {pin} status: {estado_str}")
            logging.info(f"Pin {pin} status: {estado_str}")
            return {"pin": pin, "estado": estado_str}
        elif pin == 7:  # A�adido para consultar pin 7
            estado = GPIO.input(pin)
            estado_str = "alto" if estado == GPIO.HIGH else "bajo"
            print(f"Pin {pin} status: {estado_str}")

            logging.info(f"Pin {pin} status: {estado_str}")
            return {"pin": pin, "estado": estado_str}
        else:
            logging.error(f"Pin {pin} is not configured")
            return {"error": "Invalid pin"}
    except Exception as e:
        logging.error(f"Error checking pin {pin} status: {e}")
        return {"error": str(e)}

@app.on_event("shutdown")
def cleanup_gpio():
    logging.info("Cleaning up GPIO settings")
    GPIO.cleanup()

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=4000)
