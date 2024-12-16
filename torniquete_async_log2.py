import asyncio
import aiohttp
import uuid
from datetime import datetime, timedelta
import time
import tkinter as tk
from cryptography.fernet import Fernet
from PIL import Image, ImageTk
import threading
import logging
from logging.handlers import RotatingFileHandler
import os
from functools import partial

# Configurar logging
logging.basicConfig(
    #filename='./logs/transactions.log',  # Nombre del archivo de log
    level=logging.INFO,       # Nivel de log (INFO, DEBUG, ERROR, etc.)
    format='%(asctime)s - %(levelname)s - %(message)s',  # Formato del mensaje
)

# Configuraciones
PIN = 7
SEDE = "Del Este"
API_URL = "http://127.0.0.1:4000"  # URL base de la API de manejo del relay
TORNIQUETE = "1"
FUNCION = "Entrada"
ID_SEDE_SISTEMA = "1840d65-0173-4992-af32-32aa5d730e28"
# TORNIQUETE = "Salida1"

# La clave de encriptación debe coincidir con la utilizada para encriptar el código QR
key = b'P_A-IQAqlKVctADGBFmFD_5C7yVk0EJNNBt--RqSOI0='
cipher_suite = Fernet(key)

# Cola para las transacciones
transaction_queue = asyncio.Queue()


async def procesar_codigo_qr(codigo):
    logging.debug(f"Iniciando procesamiento de código QR: {codigo}")
    try:
        # Desencriptar el código QR
        try:
            codigo_bytes = codigo.encode('utf-8')
            codigo_desencriptado_bytes = cipher_suite.decrypt(codigo_bytes)
            codigo_desencriptado = codigo_desencriptado_bytes.decode('utf-8')
            logging.info(f"Código QR desencriptado: {codigo_desencriptado}")
        except Exception as e:
            logging.error(f"Error en la desencriptación: {e}")
            raise ValueError("Código QR no puede ser desencriptado")

        # Procesar el código QR desencriptado
        partes = codigo_desencriptado.split(',')
        if len(partes) != 7:
            raise ValueError("Formato de código QR incorrecto")

        tipo = partes[0].strip()
        id_miembro = partes[1].strip()
        timestamp_milisegundos = int(partes[2].strip())
        id_sede = partes[3].strip()
        id_invitacion = partes[4].strip()
        timestamp_milisegundos2 = int(partes[5].strip())
        id_invitadoExpress = partes[6].strip()

        if tipo in ["2", "4", "6"]:
            PIN = 11
        elif tipo in ["1", "3", "5"]:
            PIN = 7
        # Funciones para encender y apagar el pin
        async def encender_pin():
            logging.debug("Intentando encender el pin")
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{API_URL}/encender/{PIN}") as response:
                    if response.status == 200:
                        logging.info(f"Pin {PIN} encendido")
                    else:
                        logging.error(f"Error al encender el pin: {response.status}")

        async def apagar_pin():
            logging.debug("Intentando apagar el pin")
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{API_URL}/apagar/{PIN}") as response:
                    if response.status == 200:
                        logging.info(f"Pin {PIN} apagado")
                    else:
                        logging.error(f"Error al apagar el pin: {response.status}")


        logging.debug(f"Tipo: {tipo}, ID Miembro: {id_miembro}, ID Sede: {id_sede}")

        # Convertir el timestamp en milisegundos a un objeto datetime
        fecha_hora = datetime.fromtimestamp(timestamp_milisegundos / 1000.0)
        fecha_hora_salida = datetime.fromtimestamp(timestamp_milisegundos2 / 1000.0)

        # Validar ID de sede
        if id_sede == "":
            id_sede=ID_SEDE_SISTEMA
        if id_sede != ID_SEDE_SISTEMA:
            logging.warning(f"ID de sede no coincide. Esperado: {ID_SEDE_SISTEMA}, Recibido: {id_sede}")
            raise ValueError("ID de sede no coincide")

        # Validar fecha y hora ingreso y salida
        ahora = datetime.now()
        rango_tiempo = timedelta(minutes=15)
        if tipo in ["1", "3", "5"]:
            if not (ahora - rango_tiempo <= fecha_hora <= ahora + rango_tiempo):
                logging.warning(f"Fecha y hora fuera de rango. Fecha: {fecha_hora}, Ahora: {ahora}")
                raise ValueError("Fecha y hora fuera de rango")
        else:
            if not (ahora - rango_tiempo <= fecha_hora_salida <= ahora + rango_tiempo):
                logging.warning(f"Fecha y hora de salida fuera de rango. Fecha: {fecha_hora_salida}, Ahora: {ahora}")
                raise ValueError("Fecha y hora fuera de rango")

        # Validaciones correctas: encender el pin y mostrar mensaje
        await encender_pin()
        ventana.after(0, lambda: lbl_mensaje.config(text="Código QR válido", fg="green"))
        await asyncio.sleep(3)
        await apagar_pin()

        # Agregar la transacción a la cola
        if tipo == "1":
            logging.debug("Agregando transacción tipo 1 a la cola")
            await transaction_queue.put(("transaccion1", id_miembro, id_sede))
        elif tipo == "2":
            logging.debug("Agregando transacción tipo 2 a la cola")
            await transaction_queue.put(("transaccion2", id_miembro, id_sede))
        elif tipo == "3":
            logging.debug("Agregando transacción tipo 3 a la cola")
            await transaction_queue.put(("transaccion3", id_miembro, id_sede, id_invitacion))
        elif tipo == "4":
            logging.debug("Agregando transacción tipo 4 a la cola")
            await transaction_queue.put(("transaccion4", id_miembro, id_sede, id_invitacion))
        elif tipo == "5":
            logging.debug("Agregando transacción tipo 5 a la cola")
            await transaction_queue.put(("transaccion5", id_miembro, id_sede, id_invitadoExpress))
        elif tipo == "6":
            logging.debug("Agregando transacción tipo 6 a la cola")
            await transaction_queue.put(("transaccion6", id_miembro, id_sede, id_invitadoExpress))
        elif tipo in ["2", "4", "6"]:
            logging.debug(f"Procesando transacción tipo {tipo}")
            ventana.after(0, lambda: lbl_mensaje.config(text="Regresa pronto...", fg="green", font=("Arial", 38)))

        # Programar la limpieza de la interfaz después de 3 segundos
        ventana.after(3000, limpiar_interfaz)
        return "success"

    except ValueError as ve:
        logging.error(f"Error de validación: {ve}")
        ventana.after(0, lambda: lbl_mensaje.config(text=f"Error: {ve}", fg="red", font=("Arial", 18)))
        await apagar_pin()
        ventana.after(3000, limpiar_interfaz)
        return "error"

    except Exception as e:
        logging.error(f"Error inesperado: {e}")
        ventana.after(0, lambda: lbl_mensaje.config(text="X", fg="red", font=("Arial", 200)))
        await apagar_pin()
        ventana.after(3000, limpiar_interfaz)
        return "error"

# =====================================================================================================
# Funciones asincrónicas para realizar transacciones
# =====================================================================================================

# Ingreso Miembros
# ========================
async def realizar_transaccion1(id_miembro, id_sede):
    logging.debug(f"Iniciando transacción 1 para miembro {id_miembro} en sede {id_sede}")
    try:
        id_transaccion = str(uuid.uuid4())
        hora_entrada = datetime.now()
        hora_entrada_texto = hora_entrada.strftime('%Y-%m-%dT%H:%M:%S')
        datos = {
            "id_miembro": id_miembro,
            "id_sede": id_sede,
            "id": id_transaccion,
            "sede": SEDE,
            "horaEntrada": hora_entrada_texto,
            "horaSalida": "",
            "tiempo": 0,
            "id_sedes": id_sede
        }
        logging.debug(f"Datos de la transacción 1: {datos}")
        async with aiohttp.ClientSession() as session:
            logging.debug("Enviando solicitud POST para transacción 1")
            async with session.post(
                'https://newo2-api-cypher.azurewebsites.net/createIngresoMiembro/',
                headers={'accept': 'application/json', 'Content-Type': 'application/json'},
                json=datos
            ) as response:
                if response.status == 200:
                    logging.info("Transacción 1 realizada con éxito")
                    ventana.after(0, lambda: lbl_mensaje.config(text="Bienvenido...", fg="green", font=("Arial", 38)))

                else:
                    logging.error(f"Error en la transacción 1: {response.status} - {await response.text()}")
    except Exception as e:
        logging.error(f"Error al realizar la transacción 1: {e}")

# Salida Miembro
# ======================
async def realizar_transaccion2(id_miembro, id_sede):
    logging.debug(f"Iniciando transacción 2 para miembro {id_miembro} en sede {id_sede}")
    ventana.after(0, lambda: lbl_mensaje.config(text="Regresa pronto...", fg="green", font=("Arial", 38)))
    try:
        id_transaccion = str(uuid.uuid4())
        hora_salida = datetime.now()
        hora_salida_texto = hora_salida.strftime('%Y-%m-%dT%H:%M:%S')
        datos = {
            "id_miembro": id_miembro,
            "hora_salida": hora_salida_texto,
            "salio": False
        }
        logging.debug(f"Datos de la transacción 2: {datos}")
        async with aiohttp.ClientSession() as session:
            logging.debug("Enviando solicitud POST para transacción 2")
            async with session.put(
                'https://newo2-api-managment.azure-api.net/cypher/updateIngresoMiembroTorniquete/',
                headers={'accept': 'application/json', 'Content-Type': 'application/json'},
                json=datos
            ) as response:
                if response.status == 200:
                    logging.info("Transacción 2 realizada con éxito")
                else:
                    logging.error(f"Error en la transacción 2: {response.status} - {await response.text()}")
    except Exception as e:
        logging.error(f"Error al realizar la transacción 2: {e}")

# Ingreso Invitado
# ======================
async def realizar_transaccion3(id_miembro, id_sede, id_invitacion):
    logging.debug(f"Iniciando transacción 3 para miembro {id_miembro} en sede {id_sede} con invitación {id_invitacion}")
    try:
        id_transaccion = str(uuid.uuid4())
        hora_entrada = datetime.now()
        hora_entrada_texto = hora_entrada.strftime('%Y-%m-%dT%H:%M:%S')
        datos = {
            "id_miembro": id_miembro,
            "id_invitados": id_invitacion,
            "id_sede": id_sede,
            "sede": SEDE,
            "id": id_transaccion,
            "horaEntrada": hora_entrada_texto,
            "horaSalida": "",
            "tiempo": 0
        }
        logging.debug(f"Datos de la transacción 3: {datos}")
        async with aiohttp.ClientSession() as session:
            logging.debug("Enviando solicitud POST para transacción 2")
            async with session.post(
                'https://newo2-api-managment.azure-api.net/cypher/ingreso_invitado/',
                headers={'accept': 'application/json', 'Content-Type': 'application/json'},
                json=datos
            ) as response:
                if response.status == 200:
                    logging.info("Transacción 3 realizada con éxito")
                    ventana.after(0, lambda: lbl_mensaje.config(text="Bienvenido...", fg="green", font=("Arial", 38)))

                else:
                    logging.error(f"Error en la transacción 3: {response.status} - {await response.text()}")
    except Exception as e:
        logging.error(f"Error al realizar la transacción 3: {e}")
        
# Salida Invitado
# ======================
async def realizar_transaccion4(id_miembro, id_sede, id_invitacion):
    logging.debug(f"Iniciando transacción 4 para miembro {id_miembro} en sede {id_sede} con la invitacion {id_invitacion}")
    ventana.after(0, lambda: lbl_mensaje.config(text="Regresa pronto...", fg="green", font=("Arial", 38)))
    try:
        id_transaccion = str(uuid.uuid4())
        hora_salida = datetime.now()
        hora_salida_texto = hora_salida.strftime('%Y-%m-%dT%H:%M:%S')
        datos = {
            "invitacion_id": id_invitacion,
            "hora_salida": hora_salida_texto,
            "salio": True
        }
        logging.debug(f"Datos de la transacción 3: {datos}")
        async with aiohttp.ClientSession() as session:
            logging.debug("Enviando solicitud POST para transacción 2")
            async with session.put(
                'https://newo2-api-managment.azure-api.net/cypher/updateIngresoInvitadoTorniquete/',
                headers={'accept': 'application/json', 'Content-Type': 'application/json'},
                json=datos
            ) as response:
                if response.status == 200:
                    logging.info("Transacción 3 realizada con éxito")
                else:
                    logging.error(f"Error en la transacción 3: {response.status} - {await response.text()}")
    except Exception as e:
        logging.error(f"Error al realizar la transacción 3: {e}")

# Ingreso Expres
# ======================
async def realizar_transaccion5(id_miembro, id_sede, id_invitacion):
    logging.debug(f"Iniciando transacción 5 para miembro {id_miembro} en sede {id_sede} con invitación {id_invitacion}")
    try:
        print("Entro Aca 1")
        hora_entrada = datetime.now()
        hora_entrada_texto = hora_entrada.strftime('%Y-%m-%dT%H:%M:%S')
        datos = {
            "id_ingresoInvitacionExpress": id_invitacion,
            "hora_entrada": hora_entrada_texto,
            "hora_salida": "",
            "salio": False
        }
        logging.debug(f"Datos de la transacción 5: {datos}")
        print(f"Datos de la transacción 5: {datos}")
        async with aiohttp.ClientSession() as session:
            logging.debug("Enviando solicitud POST para transacción 3")
            async with session.put(
                'https://newo2-api-managment.azure-api.net/cypher/updateIngresoInvitacionExpressTorniquete/',
                headers={'accept': 'application/json', 'Content-Type': 'application/json'},
                json=datos
            ) as response:
                if response.status == 200:
                    logging.info("Transacción 5 realizada con éxito")
                    ventana.after(0, lambda: lbl_mensaje.config(text="Bienvenido...", fg="green", font=("Arial", 38)))

                else:
                    logging.error(f"Error en la transacción 5: {response.status} - {await response.text()}")
    except Exception as e:
        logging.error(f"Error al realizar la transacción 5: {e}")

# Salida Invitado Expres
# ==========================
async def realizar_transaccion6(id_miembro, id_sede, id_invitacion):
    logging.debug(f"Iniciando transacción 6 para miembro {id_miembro} en sede {id_sede} con la invitacion {id_invitacion}")
    ventana.after(0, lambda: lbl_mensaje.config(text="Regresa pronto...", fg="green", font=("Arial", 38)))
    try:
        hora_entrada = datetime.now()
        hora_salida_texto = hora_entrada.strftime('%Y-%m-%dT%H:%M:%S')
        datos = {
            "id_ingresoInvitacionExpress": id_invitacion,
            "hora_salida": hora_salida_texto,
            "salio": True
        }
        logging.debug(f"Datos de la transacción 5: {datos}")
        async with aiohttp.ClientSession() as session:
            logging.debug("Enviando solicitud POST para transacción 3")
            async with session.put(
                'https://newo2-api-managment.azure-api.net/cypher/updateIngresoInvitacionExpressTorniquete/',
                headers={'accept': 'application/json', 'Content-Type': 'application/json'},
                json=datos
            ) as response:
                if response.status == 200:
                    logging.info("Transacción 6 realizada con éxito")
    except Exception as e:
        logging.error(f"Error al realizar la transacción 5: {e}")

# Función para procesar la cola de transacciones
async def procesar_cola_transacciones():
    logging.info("Iniciando procesamiento de cola de transacciones")
    while True:
        try:
            logging.debug("Esperando nueva transacción en la cola")
            transaccion = await transaction_queue.get()
            logging.debug(f"Nueva transacción recibida: {transaccion}")
            if transaccion[0] == "transaccion1":
                await realizar_transaccion1(transaccion[1], transaccion[2])
            elif transaccion[0] == "transaccion2":
                await realizar_transaccion2(transaccion[1], transaccion[2])
            elif transaccion[0] == "transaccion3":
                await realizar_transaccion3(transaccion[1], transaccion[2], transaccion[3])
            elif transaccion[0] == "transaccion4":
                await realizar_transaccion4(transaccion[1], transaccion[2], transaccion[3])
            elif transaccion[0] == "transaccion5":
                await realizar_transaccion5(transaccion[1], transaccion[2], transaccion[3])
            elif transaccion[0] == "transaccion6":
                await realizar_transaccion6(transaccion[1], transaccion[2], transaccion[3])
            transaction_queue.task_done()
            logging.debug("Transacción procesada y completada")
        except Exception as e:
            logging.error(f"Error al procesar la transacción: {e}")

# Función para limpiar la interfaz
def limpiar_interfaz():
    logging.debug("Limpiando la interfaz")
    lbl_mensaje.config(text="", font=("Arial", 18))
    entrada_codigo.delete(0, tk.END)
    entrada_codigo.focus()

# Función para manejar la entrada del código QR
def on_enter(event):
    codigo = entrada_codigo.get().strip()
    logging.debug(f"Código QR ingresado: {codigo}")
    entrada_codigo.delete(0, tk.END)
    asyncio.run_coroutine_threadsafe(procesar_codigo_qr(codigo), loop)

# Función para ejecutar el bucle de eventos asyncio en un hilo separado
# def run_async_loop(loop):
#     asyncio.set_event_loop(loop)
#     loop.run_forever()

# Configuración de la interfaz gráfica
ventana = tk.Tk()
ventana.title("NEWO - Sistema de Control de Acceso")
ventana.geometry("640x480")
ventana.configure(bg="black")  # Fondo negro

# Cargar y redimensionar la imagen
imagen = Image.open("NEWO.png")
imagen = imagen.resize((250, 250), Image.Resampling.LANCZOS)
imagen_tk = ImageTk.PhotoImage(imagen)
# Etiqueta para mostrar la imagen
lbl_imagen = tk.Label(ventana, image=imagen_tk, bg="black")
lbl_imagen.pack(pady=10)

lbl_codigo = tk.Label(ventana, text="Escanee el código QR:", fg="white", bg="black", font=("Arial", 18))
lbl_codigo.pack(pady=10)

lbl_mensaje = tk.Label(ventana, text="", fg="black", bg="black", font=("Arial", 18))
entrada_codigo = tk.Entry(ventana, font=("Arial", 8), bg="black", fg="black", bd=0, insertbackground="black")
entrada_codigo.pack(pady=20)
entrada_codigo.focus()

lbl_mensaje = tk.Label(ventana, text="", fg="white", bg="black", font=("Arial", 18))
lbl_mensaje.pack(pady=10)

# Vincular la función de procesamiento al evento de entrada de texto
entrada_codigo.bind("<Return>", on_enter)

# Mantener el cursor en el campo de texto
entrada_codigo.focus_set()

# Función para ejecutar el bucle de eventos asyncio en un hilo separado
def run_async_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

# Crear un nuevo bucle de eventos para el hilo asyncio
loop = asyncio.new_event_loop()

# Iniciar el bucle asyncio en un hilo separado
threading.Thread(target=run_async_loop, args=(loop,), daemon=True).start()

# Agregar la tarea de procesar la cola de transacciones al bucle asyncio
asyncio.run_coroutine_threadsafe(procesar_cola_transacciones(), loop)

logging.info("Iniciando la aplicación")
# Iniciar el bucle principal de Tkinter
ventana.mainloop()