import socket
import threading
import os
import ssl
from datetime import datetime

# Candados (Mutex) para sincronización
candado_archivos = threading.Lock()
candado_log = threading.Lock()

# Directorios obligatorios según la guía
BASE_DIR = "/home/crank/ftps/servidor_archivos"
DIR_ENTRADA = os.path.join(BASE_DIR, "entrada")
DIR_PROCESADOS = os.path.join(BASE_DIR, "procesados")
DIR_LOGS = os.path.join(BASE_DIR, "logs")
RUTA_LOG = os.path.join(DIR_LOGS, "registro.log")

# Asegurar que existan todas las carpetas requeridas
os.makedirs(DIR_ENTRADA, exist_ok=True)
os.makedirs(DIR_PROCESADOS, exist_ok=True)
os.makedirs(DIR_LOGS, exist_ok=True)

# Certificados SSL/TLS
CERT_FILE = "/home/crank/ftps/servidor/certs/servidor.crt"
KEY_FILE = "/home/crank/ftps/servidor/certs/servidor.key"

def registrar_operacion(cliente, operacion):
    """Escribe de forma sincronizada en el archivo registro.log"""
    fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linea = f"[{fecha_hora}] Cliente {cliente} -> {operacion}\n"
    
    with candado_log:  # Sincronización para evitar corrupción del LOG
        with open(RUTA_LOG, "a", encoding="utf-8") as f:
            f.write(linea)

def manejar_cliente(ssl_client_socket, client_address):
    id_cliente = f"{client_address[0]}:{client_address[1]}"
    print(f"[+] Hilo activo y SEGURO para {id_cliente}")
    registrar_operacion(id_cliente, "Conexión establecida de forma segura")
    
    try:
        ssl_client_socket.send(b"Bienvenido al Sistema de Gestion de Archivos Remoto FTPS.\n")
        ssl_client_socket.send(b"Comandos: LIST, UPLOAD <archivo>, DOWNLOAD <archivo>, LOGS, salir\n\n")
        
        while True:
            datos = ssl_client_socket.recv(1024)
            if not datos:
                break
                
            comando = datos.decode('utf-8').strip()
            print(f"[{id_cliente}] Comando: {comando}")
            
            # --- COMANDO: LIST ---
            if comando.upper() == "LIST":
                with candado_archivos:  # Evita lectura mientras el demonio o un upload modifican
                    archivos = os.listdir(DIR_ENTRADA)
                
                if not archivos:
                    respuesta = "La carpeta 'entrada' esta vacia.\n"
                else:
                    respuesta = "Archivos en carpeta 'entrada':\n" + "\n".join(archivos) + "\n"
                
                ssl_client_socket.send(respuesta.encode('utf-8'))
                registrar_operacion(id_cliente, "Solicitó LIST de la carpeta entrada")
            
            # --- COMANDO: UPLOAD ---
            elif comando.upper().startswith("UPLOAD "):
                nombre_archivo = comando.split(" ", 1)[1].strip()
                ruta_final = os.path.join(DIR_ENTRADA, nombre_archivo) # Sube a 'entrada' según diseño
                
                ssl_client_socket.send(b"READY")
                bytes_archivo = ssl_client_socket.recv(4096)
                
                with candado_archivos:
                    with open(ruta_final, "wb") as f:
                        f.write(bytes_archivo)
                
                respuesta = f"Archivo '{nombre_archivo}' subido a 'entrada' exitosamente.\n"
                ssl_client_socket.send(respuesta.encode('utf-8'))
                registrar_operacion(id_cliente, f"Subió el archivo '{nombre_archivo}'")

            # --- COMANDO: DOWNLOAD ---
            elif comando.upper().startswith("DOWNLOAD "):
                nombre_archivo = comando.split(" ", 1)[1].strip()
                ruta_archivo = os.path.join(DIR_ENTRADA, nombre_archivo)
                
                with candado_archivos:
                    existe = os.path.exists(ruta_archivo)
                
                if existe:
                    ssl_client_socket.send(b"READY")
                    with candado_archivos:
                        with open(ruta_archivo, "rb") as f:
                            bytes_archivo = f.read()
                    ssl_client_socket.sendall(bytes_archivo)
                    registrar_operacion(id_cliente, f"Descargó el archivo '{nombre_archivo}'")
                else:
                    ssl_client_socket.send(b"ERROR: El archivo no existe en el servidor.")
            
            # --- COMANDO: LOGS ---
            elif comando.upper() == "LOGS":
                with candado_log:
                    if os.path.exists(RUTA_LOG):
                        with open(RUTA_LOG, "r", encoding="utf-8") as f:
                            contenido = f.read()
                    else:
                        contenido = "No hay registros aun.\n"
                ssl_client_socket.send(f"--- LOG DE OPERACIONES ---\n{contenido}\n".encode('utf-8'))
                registrar_operacion(id_cliente, "Consultó los logs del sistema")

            # --- COMANDO: SALIR ---
            elif comando.lower() == "salir":
                ssl_client_socket.send(b"Desconectando de forma segura... Adios!\n")
                registrar_operacion(id_cliente, "Se desconectó del servidor")
                break
            else:
                ssl_client_socket.send(b"Comando no reconocido.\n")
                
    except Exception as e:
        print(f"[-] Error seguro con cliente {id_cliente}: {e}")
    finally:
        ssl_client_socket.close()
        print(f"[-] Conexión segura cerrada con {client_address[0]}")

def iniciar_servidor():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('0.0.0.0', 8080))
    server_socket.listen(5)
    
    contexto_ssl = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    contexto_ssl.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)
    
    print(f"[*] Servidor FTPS escuchando en el puerto 8080...")
    
    try:
        while True:
            client_socket, client_address = server_socket.accept()
            try:
                ssl_client_socket = contexto_ssl.wrap_socket(client_socket, server_side=True)
                hilo = threading.Thread(target=manejar_cliente, args=(ssl_client_socket, client_address))
                hilo.start()
            except Exception as ssl_error:
                client_socket.close()
    except KeyboardInterrupt:
        print("\n[*] Apagando servidor seguro...")
    finally:
        server_socket.close()

if __name__ == "__main__":
    iniciar_servidor()