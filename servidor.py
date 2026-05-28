import socket
import threading
import os
import ssl  # <--- IMPORTANTE: Librería de seguridad de Python

candado_servidor = threading.Lock()
CARPETA_STORAGE = "servidor/storage"
os.makedirs(CARPETA_STORAGE, exist_ok=True)

# --- REEMPLAZA LAS RUTAS CON ESTAS FIJAS ---
CERT_FILE = "/home/crank/ftps/servidor/certs/servidor.crt"
KEY_FILE = "/home/crank/ftps/servidor/certs/servidor.key"
CARPETA_STORAGE = "/home/crank/ftps/servidor/storage"

def manejar_cliente(ssl_client_socket, client_address):
    print(f"[+] Hilo activo y SEGURO para {client_address[0]}:{client_address[1]}")
    
    try:
        ssl_client_socket.send(b"Bienvenido al servidor FTPS SEGURO (SSL/TLS).\n")
        ssl_client_socket.send(b"Comandos disponibles: LIST, salir\n\n")
        
        while True:
            datos = ssl_client_socket.recv(1024)
            if not datos:
                break
                
            comando = datos.decode('utf-8').strip()
            print(f"[{client_address[0]}:{client_address[1]}] Comando encriptado: {comando}")
            
            if comando.upper() == "LIST":
                with candado_servidor:
                    archivos = os.listdir(CARPETA_STORAGE)
                
                if len(archivos) == 0:
                    respuesta = "El servidor esta vacio.\n"
                else:
                    respuesta = "Archivos en el servidor:\n" + "\n".join(archivos) + "\n"
                
                ssl_client_socket.send(respuesta.encode('utf-8'))
            
            elif comando.lower() == "salir":
                ssl_client_socket.send(b"Desconectando de forma segura... Adios!\n")
                break
            else:
                ssl_client_socket.send(b"Comando no reconocido. Prueba con LIST o salir.\n")
                
    except Exception as e:
        print(f"[-] Error seguro con cliente {client_address}: {e}")
    finally:
        ssl_client_socket.close()
        print(f"[-] Conexión segura cerrada con {client_address[0]}")

def iniciar_servidor():
    # 1. Crear el socket TCP normal
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('0.0.0.0', 8080))
    server_socket.listen(5)
    
    # 2. Configurar el contexto de seguridad SSL/TLS del servidor
    # Usamos PROTOCOL_TLS_SERVER que es el estándar moderno de seguridad
    contexto_ssl = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    contexto_ssl.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)
    
    print(f"[*] Servidor FTPS escuchando con HILOS y CIFRADO SSL/TLS en el puerto 8080...")
    
    try:
        while True:
            # El socket recibe la conexión inicial en texto plano...
            client_socket, client_address = server_socket.accept()
            print(f"\n[!] Conexión entrante de {client_address[0]}. Iniciando cifrado...")
            
            try:
                # ...y AQUÍ envolvemos el socket con SSL para hacer el "Handshake" (apretón de manos)
                ssl_client_socket = contexto_ssl.wrap_socket(client_socket, server_side=True)
                
                # Pasamos el socket encriptado al hilo
                hilo = threading.Thread(target=manejar_cliente, args=(ssl_client_socket, client_address))
                hilo.start()
            except Exception as ssl_error:
                print(f"[-] Falló el apretón de manos SSL con {client_address}: {ssl_error}")
                client_socket.close()
                
    except KeyboardInterrupt:
        print("\n[*] Apagando servidor seguro...")
    finally:
        server_socket.close()

if __name__ == "__main__":
    iniciar_servidor()
