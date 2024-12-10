from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import serial

app = FastAPI()

# Configuración de CORS
origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:3000",
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configura el puerto serial para comunicarte con el módulo de relé
ser = serial.Serial('COM3', 9600)  # Ajusta el puerto y la velocidad de baudios según tu configuración

def encender_pin(pin: int):
    ser.write(f'ENCENDER {pin}\n'.encode())  # Enviar el comando para encender el pin
    return {"pin": pin, "estado": "encendido"}

def apagar_pin(pin: int):
    ser.write(f'APAGAR {pin}\n'.encode())  # Enviar el comando para apagar el pin
    return {"pin": pin, "estado": "apagado"}

def obtener_estado_pin(pin: int):
    ser.write(f'CONSULTAR {pin}\n'.encode())  # Enviar el comando para consultar el estado del pin
    estado = ser.readline().decode().strip()  # Leer la respuesta del módulo
    return {"pin": pin, "estado": estado}

@app.get("/encender/{pin}")
def encender(pin: int):
    return encender_pin(pin)

@app.get("/apagar/{pin}")
def apagar(pin: int):
    return apagar_pin(pin)

@app.get("/consultar/{pin}")
def consultar(pin: int):
    return obtener_estado_pin(pin)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=4000)
## para ejecutar uvicorn servicio:app --reload --host 127.0.0.1 --port 4000     