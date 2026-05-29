import os
import time
import threading
import shutil
from datetime import datetime

# Rutas de sincronización (Deben ser las mismas del servidor)
BASE_DIR = "/home/crank/ftps/servidor_archivos"
DIR_ENTRADA = os.path.join(BASE_DIR, "entrada")
DIR_PROCESADOS = os.path.join(BASE_DIR, "procesados")
DIR_LOGS = os.path.join(BASE_DIR, "logs")
RUTA_LOG = os.path.join(DIR_LOGS, "registro.log")

# Mutex compartido mentalmente por el sistema de archivos
candado_archivos = threading.Lock()
candado_log = threading.Lock()

def registrar_accion_demonio(accion):
    fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linea = f"[{fecha_hora}] [DEMONIO] -> {accion}\n"
    with candado_log:
        with open(RUTA_LOG, "a", encoding="utf-8") as f:
            f.write(linea)

def procesar_archivo_trabajador(nombre_archivo):
    """Función que ejecuta el hilo para procesar un archivo"""
    ruta_origen = os.path.join(DIR_ENTRADA, nombre_archivo)
    ruta_destino = os.path.join(DIR_PROCESADOS, nombre_archivo)
    
    print(f"[DEMONIO-THREAD] Procesando archivo: {nombre_archivo}")
    # Simula que hace algún procesamiento pesado en el archivo (ej: compresión o análisis)
    time.sleep(2) 
    
    # Sección Crítica: Mover el archivo de forma segura usando el Lock
    with candado_archivos:
        if os.path.exists(ruta_origen):
            shutil.move(ruta_origen, r_destino := ruta_destino)
            print(f"[DEMONIO-THREAD] Moviendo {nombre_archivo} a 'procesados'.")
            registrar_accion_demonio(f"Archivo '{nombre_archivo}' procesado y movido a 'procesados'")

def ejecutar_demonio():
    print("[*] Proceso demonio iniciado. Monitoreando 'entrada' cada 10 segundos...")
    registrar_accion_demonio("Demonio de procesamiento iniciado.")
    
    try:
        while True:
            # Sección Crítica: Listar de forma segura
            with candado_archivos:
                archivos = os.listdir(DIR_ENTRADA)
            
            if archivos:
                print(f"[!] Demonio detectó {len(archivos)} archivos nuevos en 'entrada'.")
                for archivo in archivos:
                    # Lanzar un hilo independiente por cada archivo para procesarlo en paralelo
                    hilo_procesador = threading.Thread(target=procesar_archivo_trabajador, args=(archivo,))
                    hilo_procesador.start()
            
            # Esperar 10 segundos antes de la siguiente revisión
            time.sleep(10)
    except KeyboardInterrupt:
        print("\n[*] Apagando demonio de procesamiento...")
        registrar_accion_demonio("Demonio de procesamiento apagado.")

if __name__ == "__main__":
    # Asegurar entornos creados
    os.makedirs(DIR_ENTRADA, exist_ok=True)
    os.makedirs(DIR_PROCESADOS, exist_ok=True)
    os.makedirs(DIR_LOGS, exist_ok=True)
    ejecutar_demonio()
