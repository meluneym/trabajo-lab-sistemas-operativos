import socket

def iniciar_servidor():
    # 1. Crear el socket (IPv4, TCP)
    # socket.AF_INET = IPv4, socket.SOCK_STREAM = TCP
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Reutilizar el puerto si se cierra inesperadamente durante las pruebas
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # 2. Asignar IP y Puerto (Escucha en todas las interfaces de tu máquina en el puerto 8080)
    HOST = '0.0.0.0'
    PORT = 8080
    server_socket.bind((HOST, PORT))
    
    # 3. Poner el servidor en modo escucha (Cola de espera de hasta 5 conexiones)
    server_socket.listen(5)
    print(f"[*] Servidor FTPS base escuchando en {HOST}:{PORT}...")
    
    try:
        while True:
            # 4. Aceptar una nueva conexión (El programa se detiene aquí hasta que alguien se conecta)
            client_socket, client_address = server_socket.accept()
            print(f"[+] Conexión aceptada desde {client_address[0]}:{client_address[1]}")
            
            # Mensaje de bienvenida que recibirá quien se conecte
            client_socket.send(b"Bienvenido al servidor FTPS experimental.\n")
            
            # Cerrar la conexión por ahora (en los siguientes pasos aquí meteremos los hilos)
            client_socket.close()
            print(f"[-] Conexión cerrada con {client_address[0]}\n")
            
    except KeyboardInterrupt:
        print("\n[*] Apagando el servidor de forma segura...")
    finally:
        server_socket.close()

if __name__ == "__main__":
    iniciar_servidor()
