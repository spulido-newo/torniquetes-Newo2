import pyudev
import time

def detectar_lector():
    # Crear contexto udev para listar los dispositivos
    context = pyudev.Context()

    # Filtrar dispositivos HID
    for device in context.list_devices(subsystem='hidraw'):
        device_node = device.device_node  # Obtiene la ruta del dispositivo
        print(f"Dispositivo encontrado: {device_node}")
        print(f"Detalles del dispositivo: {device}")

        # Verificar el Vendor ID y Model ID del dispositivo
        vendor_id = device.get('ID_VENDOR_ID', '')
        model_id = device.get('ID_MODEL_ID', '')
        print(f"Vendor ID: {vendor_id}, Model ID: {model_id}")
        
        # Intentamos acceder a la ruta del dispositivo
        try:
            with open(device_node, 'rb') as f:
                # Intentamos leer datos del dispositivo
                data = f.read(64)  # Lee los primeros 64 bytes (puedes ajustar el tama�o seg�n sea necesario)
                if data:
                    print(f"Lectura exitosa desde {device_node}: {data}")
                    return device_node
        except Exception as e:
            print(f"No se pudo leer desde {device_node}: {e}")

    # Si no se encontr� ning�n lector adecuado
    return None

def main():
    lector_path = detectar_lector()
    if lector_path:
        print(f"Dispositivo encontrado en: {lector_path}")
    else:
        print("No se encontr� ning�n lector de QR adecuado.")

if __name__ == "__main__":
    main()
