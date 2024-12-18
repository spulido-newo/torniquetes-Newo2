from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import RPi.GPIO as GPIO
import logging
import uvicorn

# Configuraci�n del logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Inicializaci�n de la aplicaci�n FastAPI
app = FastAPI()

# Configuraci�n de CORS
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuraci�n de GPIO
GPIO.setmode(GPIO.BCM)

# Pines GPIO
PIN_4 = 4   # GPIO 4 (Posici�n 7 en el header)
PIN_17 = 17 # GPIO 17 (para referencia)

# Configuraci�n de los pines
GPIO.setup(PIN_4, GPIO.OUT)   # Configura GPIO 4 como salida
GPIO.setup(PIN_17, GPIO.OUT)  # Configura GPIO 17 como salida

# Endpoint para encender un pin de salida
@app.get("/encender/{pin}")
def encender(pin: int):
    try:
        if pin in [PIN_4, PIN_17]:  # Verificamos si es un pin permitido
            GPIO.output(pin, GPIO.HIGH)
            logging.info(f"Pin {pin} encendido")
            return {"pin": pin, "estado": "encendido"}
        else:
            return {"error": f"El pin {pin} no est� configurado como salida"}
    except Exception as e:
        logging.error(f"Error al encender el pin {pin}: {e}")
        return {"error": str(e)}


# Endpoint para apagar un pin de salida
@app.get("/apagar/{pin}")
def apagar(pin: int):
    try:
        if pin in [PIN_4, PIN_17]:  # Verificamos si es un pin permitido
            GPIO.output(pin, GPIO.LOW)
            logging.info(f"Pin {pin} apagado")
            return {"pin": pin, "estado": "apagado"}
        else:
            return {"error": f"El pin {pin} no est� configurado como salida"}
    except Exception as e:
        logging.error(f"Error al apagar el pin {pin}: {e}")
        return {"error": str(e)}


# Endpoint para consultar el estado de un pin
@app.get("/consultar/{pin}")
def consultar(pin: int):
    try:
        if pin in [PIN_4, PIN_17]:
            estado = GPIO.input(pin)
            estado_str = "alto" if estado == GPIO.HIGH else "bajo"
            logging.info(f"El pin {pin} est� {estado_str}")
            return {"pin": pin, "estado": estado_str}
        else:
            return {"error": f"El pin {pin} no est� configurado"}
    except Exception as e:
        logging.error(f"Error al consultar el pin {pin}: {e}")
        return {"error": str(e)}

# Limpiar configuraci�n de GPIO al cerrar la aplicaci�n
@app.on_event("shutdown")
def cleanup_gpio():
    logging.info("Limpiando configuraci�n GPIO")
    GPIO.cleanup()

# Ejecutar la aplicaci�n FastAPI
if __name__ == '__main__':
    try:
        uvicorn.run(app, host='0.0.0.0', port=4000)
    except KeyboardInterrupt:
        logging.info("Aplicaci�n detenida manualmente")
        GPIO.cleanup()
