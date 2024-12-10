from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import serial
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
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serial port configuration
try:
    ser = serial.Serial('COM3', 9600)  # Adjust COM port and baud rate as needed
    logging.info(f"Serial port {ser.port} opened successfully")
except serial.SerialException as e:
    logging.error(f"Error opening serial port: {e}")
    ser = None

@app.get("/encender/{pin}")
def encender(pin: int):
    try:
        if ser:
            ser.write(f'ENCENDER {pin}\n'.encode())
            logging.info(f"Pin {pin} turned on")
            return {"pin": pin, "estado": "encendido"}
        else:
            logging.error("Serial port not available")
            return {"error": "Serial port not available"}
    except Exception as e:
        logging.error(f"Error turning on pin {pin}: {e}")
        return {"error": str(e)}

@app.get("/apagar/{pin}")
def apagar(pin: int):
    try:
        if ser:
            ser.write(f'APAGAR {pin}\n'.encode())
            logging.info(f"Pin {pin} turned off")
            return {"pin": pin, "estado": "apagado"}
        else:
            logging.error("Serial port not available")
            return {"error": "Serial port not available"}
    except Exception as e:
        logging.error(f"Error turning off pin {pin}: {e}")
        return {"error": str(e)}

@app.get("/consultar/{pin}")
def consultar(pin: int):
    try:
        if ser:
            ser.write(f'CONSULTAR {pin}\n'.encode())
            estado = ser.readline().decode().strip()
            logging.info(f"Pin {pin} status: {estado}")
            return {"pin": pin, "estado": estado}
        else:
            logging.error("Serial port not available")
            return {"error": "Serial port not available"}
    except Exception as e:
        logging.error(f"Error checking pin {pin} status: {e}")
        return {"error": str(e)}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=4000)