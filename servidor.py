import socket
import threading
import os

# Crear un "Candado" (Mutex) global para la sincronización
candado_servidor = threading.Lock()

# Asegurarnos de que exista la carpeta donde se guardarán los archivos del FTP
CARPETA_STORAGE = "servidor/storage"
os.makedirs(CARPETA_STORAGE, exist_ok=True)

def manejar_cliente(client_socket, client_address):
    print(f"[+] Hilo activo para {client_address[0]}:{client_address[1]}")
    
    try:
        client_socket.send(b"Bienvenido al mini-servidor FTPS.\n")
        client_socket.send(b"Comandos disponibles: LIST, salir\n\n")
        
        while True:
            datos = client_socket.recv(1024)
            if not datos:
                break
                
            comando = datos.decode('utf-8').strip()
            print(f"[{client_address[0]}:{client_address[1]}] Comando recibido: {comando}")
            
            # --- COMANDO: LIST ---
            if comando.upper() == "LIST":
                # Usamos el candado para asegurarnos de que nadie esté borrando o
                # modificando la carpeta mientras leemos la lista de archivos
                with candado_servidor:
                    archivos = os.listdir(CARPETA_STORAGE)
                
                if len(archivos) == 0:
                    respuesta = "El servidor esta vacio.\n"
                else:
                    respuesta = "Archivos en el servidor:\n" + "\n".join(archivos) + "\n"
                
                client_socket.send(respuesta.encode('utf-8'))
            
            # --- COMANDO: SALIR ---
            elif comando.lower() == "salir":
                client_socket.send(b"Desconectando... Adios!\n")
                break
                
            else:
                client_socket.send(b"Comando no reconocido. Prueba con LIST o salir.\n")
                
    except Exception as e:
        print(f"[-] Error con cliente {client_address}: {e}")
    finally:
        client_socket.close()
        print(f"[-] Hilo finalizado para {client_address[0]}")

def iniciar_servidor():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('0.0.0.0', 8080))
    server_socket.listen(5)
    print(f"[*] Servidor FTPS escuchando y protegido con MUTEX en el puerto 8080...")
    
    try:
        while True:
            client_socket, client_address = server_socket.accept()
            hilo = threading.Thread(target=manejar_cliente, args=(client_socket, client_address))
            hilo.start()
    except KeyboardInterrupt:
        print("\n[*] Apagando servidor...")
    finally:
        server_socket.close()

if __name__ == "__main__":
    iniciar_servidor()
