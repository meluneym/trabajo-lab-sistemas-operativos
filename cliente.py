import socket
import ssl
import os

def iniciar_cliente():
    HOST = '127.0.0.1'
    PORT = 8080

    contexto_ssl = ssl.create_default_context()
    contexto_ssl.check_hostname = False
    contexto_ssl.verify_mode = ssl.CERT_NONE

    print("[*] Conectando al servidor FTPS seguro...")

    try:
        sock_plano = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock_seguro = contexto_ssl.wrap_socket(sock_plano, server_hostname=HOST)
        sock_seguro.connect((HOST, PORT))
        print("[+] ¡Conexión segura SSL/TLS establecida!\n")

        bienvenida = sock_seguro.recv(2048).decode('utf-8')
        print(bienvenida)

        while True:
            comando = input("FTPS_Client> ").strip()
            if not comando:
                continue
                
            # --- LOGICA UPLOAD ---
            if comando.upper().startswith("UPLOAD "):
                nombre_archivo = comando.split(" ", 1)[1].strip()
                if not os.path.exists(nombre_archivo):
                    print(f"[-] Error: El archivo local '{nombre_archivo}' no existe.")
                    continue
                
                sock_seguro.send(comando.encode('utf-8'))
                confirmacion = sock_seguro.recv(1024).decode('utf-8')
                if confirmacion == "READY":
                    with open(nombre_archivo, "rb") as f:
                        sock_seguro.sendall(f.read())
                    respuesta = sock_seguro.recv(1024).decode('utf-8')
                    print(respuesta)

            # --- LOGICA DOWNLOAD ---
            elif comando.upper().startswith("DOWNLOAD "):
                nombre_archivo = comando.split(" ", 1)[1].strip()
                sock_seguro.send(comando.encode('utf-8'))
                
                confirmacion = sock_seguro.recv(1024).decode('utf-8')
                if confirmacion == "READY":
                    # Recibimos el contenido y lo guardamos localmente con prefijo 'descargado_'
                    bytes_archivo = sock_seguro.recv(4096)
                    with open(f"descargado_{nombre_archivo}", "wb") as f:
                        f.write(bytes_archivo)
                    print(f"[+] Archivo '{nombre_archivo}' descargado con éxito como 'descargado_{nombre_archivo}'.")
                else:
                    print(confirmacion) # Imprime el mensaje de error del servidor

            # --- LOGICA RESTO DE COMANDOS ---
            else:
                sock_seguro.send(comando.encode('utf-8'))
                respuesta = sock_seguro.recv(4096).decode('utf-8')
                print(respuesta)
                if comando.lower() == "salir":
                    break

    except Exception as e:
        print(f"[-] Error en el cliente: {e}")
    finally:
        if 'sock_seguro' in locals():
            sock_seguro.close()
        print("[*] Conexión finalizada.")

if __name__ == "__main__":
    iniciar_cliente()
