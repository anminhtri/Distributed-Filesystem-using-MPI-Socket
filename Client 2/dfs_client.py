import socket
import sys
import os
import pickle

def name_node(sock, proc):
    sock.send(proc.encode())
    sock.recv(1024)
    data = sock.recv(1024)
    data = pickle.loads(data)
    for server, files in data.items():
        print(f"{server}:")
        for file, (content, file_size) in files.items():
            print(f"    {file} - size: {file_size}")

def receive_file(sock, file_path, proc):
    file_name = proc + file_path
    sock.send(file_name.encode())
    sock.recv(1024)
    file_size = int(sock.recv(1024).decode())

    sock.send(b'OK')

    # Receive and save file
    print(f"Receiving file {file_path}...")
    received_size = 0
    with open(file_path, "wb") as file:
        while received_size < file_size:
            remaining_size = file_size - received_size
            chunk_size = min(1024, remaining_size)
            data = sock.recv(chunk_size)
            if not data:
                break
            file.write(data)
            received_size += len(data)
    print(f"File {file_path} received and saved")

def upload_file(sock, file_path, proc):
    file_name = proc + os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    sock.sendall(file_name.encode())
    sock.recv(1024) 
    sock.sendall(str(file_size).encode())
    sock.recv(1024) 

    with open(file_path, "rb") as file:
        while True:
            data = file.read(1024)
            if not data:
                break
            sock.sendall(data)
    print(f"File {file_path} uploaded successfully")

def main():
    if len(sys.argv) == 4 and (sys.argv[3] == "-r" or sys.argv[3] == "-a"):
        server_index = int(sys.argv[1])
        file_path = sys.argv[2]
        proc = sys.argv[3]

        server_ip = "localhost" 
        server_port = 12345 + server_index  

        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((server_ip, server_port))

        if proc == "-r":
            receive_file(client_socket, file_path, proc)

        if proc == "-a":
            upload_file(client_socket, file_path, proc)

    elif len(sys.argv) == 2 and sys.argv[1] == "list":
        proc = sys.argv[1]

        server_ip = "localhost" 
        server_port = 12345

        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((server_ip, server_port))
        name_node(client_socket, proc)

    client_socket.close()

if __name__ == "__main__":
    main()