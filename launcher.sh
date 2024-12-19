#!/bin/bash

# Ejecuta el primer comando en una nueva terminal y deja la terminal abierta
/usr/bin/lxterminal -e "bash -c '/home/admin/newo2/torniquetes-Newo2/venv/bin/python /home/admin/newo2/torniquetes-Newo2/servicio.py; echo Presiona Enter para cerrar; read'" &

# Espera un par de segundos para evitar conflictos
sleep 2

# Ejecuta el segundo comando en otra nueva terminal y deja la terminal abierta
/usr/bin/lxterminal -e "bash -c '/home/admin/newo2/torniquetes-Newo2/venv/bin/python /home/admin/newo2/torniquetes-Newo2/torniquete_async_log2.py; echo Presiona Enter para cerrar; read'" &
