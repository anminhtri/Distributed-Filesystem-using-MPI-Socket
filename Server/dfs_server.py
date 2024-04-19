import socket
import sys
import os
import threading
import pickle
import stat
import time
from mpi4py import MPI

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()
data_num = 3

PORT = 12345 + rank

if rank != 0:
    SERVER_DIRECTORY = f"data_node{rank}"

if rank == 0 and size > data_num+1:
    print("the amount of processors is larger than of data nodes")
    sys.exit()
elif size > data_num+1: 
    sys.exit()

server_file_contents = {}

def load_server_file_contents(directory):
    global server_file_contents
    for file_name in os.listdir(directory):
        file_path = os.path.join(directory, file_name)
        with open(file_path, "rb") as file:
            file_content = file.read()
            file_size = len(file_content)
            server_file_contents[file_name] = (file_content, file_size)
    comm.send(server_file_contents, dest=0)

def send_file(conn, file_content):
    conn.sendall(file_content)

def total_size (server_file_contents):
    total = sum(size for _, (_, size) in server_file_contents.items())
    return total

def get_meta (directory, file_name):
    file_path = os.path.join(directory, file_name)
    file_stat = os.stat(file_path)

    file_size = file_stat[stat.ST_SIZE]
    last_modified_time = file_stat[stat.ST_MTIME]
    last_access_time = file_stat[stat.ST_ATIME]

    last_modified_time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(last_modified_time))
    last_access_time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(last_access_time))

    return [file_name, file_size, last_modified_time_str, last_access_time_str]

def handle_file_request(conn, file_name):
    for i in range(1,size):
        server_file_contents[i] = (comm.recv(source=i))    
    for i in range(1,size):
        comm.send(file_name, dest=i)
    requested_file = []
    requested_file = comm.recv(source=MPI.ANY_SOURCE)
    if len(requested_file) != 0:
        file_content, file_size = requested_file
        conn.sendall(str(file_size).encode())
        conn.recv(1024)  
        send_file(conn, file_content)
        print(f"Sent file {file_name} to client")
    else:
        print(f"File {file_name} not found")

def handle_file_upload(conn, file_name):
    for i in range(1,size):
        server_file_contents[i] = (comm.recv(source=i))
    for i in range(1,size):
        comm.send(file_name, dest=i)
    indices = []
    for i in range(1,size):
        indices.append(comm.recv(source=i))
    index1 = sum(indices)
    rep_file = f"rep{index1}_"+file_name

    for i in range(1,size):
        comm.send(rep_file, dest=i)
    indices = []
    for i in range(1,size):
        indices.append(comm.recv(source=i))
    index2 = sum(indices)

    storages = []
    for i in range(1,size):
        storages.append(comm.recv(source=i))
    indexed_list = list(enumerate(storages))
    sorted_indexed_list = sorted(indexed_list, key=lambda x: x[1])
    sorted_indices = [index for index, _ in sorted_indexed_list]

    file_size = int(conn.recv(1024).decode())
    conn.send(b"OK")  

    received_size = 0
    file_content = b""
    while received_size < file_size:
        remaining_size = file_size - received_size
        chunk_size = min(1024, remaining_size)
        data = conn.recv(chunk_size)
        if not data:
            break
        file_content += data
        received_size += len(data)
    
    if index1 > 0 and index2 > 0:
        for i in range(len(sorted_indices)):
            if index1-1 == sorted_indices[i]:
                sorted_indices[i] = sorted_indices[0]
                sorted_indices[0] = index1-1
            if index2-1 == sorted_indices[i]:
                sorted_indices[i] = sorted_indices[1]
                sorted_indices[1] = index2-1
    
    comm.send(file_content, dest=sorted_indices[0]+1)
    comm.send(file_name, dest=sorted_indices[0]+1)
    comm.send(file_content, dest=sorted_indices[1]+1)
    comm.send(f"rep{sorted_indices[0]+1}_"+file_name, dest=sorted_indices[1]+1)
    for i in range(2,size-1):
        comm.send("", dest=sorted_indices[i]+1)
        comm.send("", dest=sorted_indices[i]+1)

def handle_client_connection(conn):
    print("Connection established")
    while True:
        request = conn.recv(1024).decode()
        conn.send(b"OK")
        if request != "list":
            signal = request[:2]
            file_name = request[2:]
            if not file_name:
                break
            if signal == "-r":
                for i in range(1, size):    
                    comm.send(signal, dest=i)
                handle_file_request(conn, file_name)
            if signal == "-a":
                for i in range(1, size):    
                    comm.send(signal, dest=i)
                handle_file_upload(conn, file_name)
            if signal == "-m":
                for i in range(1, size):    
                    comm.send(signal, dest=i)
                for i in range(1,size):
                    server_file_contents[i] = (comm.recv(source=i))    
                for i in range(1,size):
                    comm.send(file_name, dest=i)
                meta = comm.recv(source=MPI.ANY_SOURCE)
                meta = pickle.dumps(meta)
                send_file(conn, meta)
        else:
            for i in range(1, size):    
                comm.send(request, dest=i)
            for i in range(1,size):
                server_file_contents[i] = (comm.recv(source=i))
            contents = pickle.dumps(server_file_contents)
            send_file(conn, contents)

def start_server(port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', port))
    server_socket.listen(1)
    print(f"Server listening on port {port}")

    while True:
        conn, addr = server_socket.accept()
        thread = threading.Thread(target=handle_client_connection, args=(conn,))
        thread.start()

def main():
    if rank != 0:
        load_server_file_contents(SERVER_DIRECTORY)
        while True: 
            trigger = comm.recv(source=0)
            if trigger == "list":
                load_server_file_contents(SERVER_DIRECTORY)
            elif trigger == "-r":
                load_server_file_contents(SERVER_DIRECTORY)
                requested_file = comm.recv(source=0)
                if requested_file in server_file_contents:
                    comm.send(server_file_contents[requested_file], dest=0)
            elif trigger == "-a":
                load_server_file_contents(SERVER_DIRECTORY)
                requested_file = comm.recv(source=0)
                if requested_file in server_file_contents:
                    comm.send(rank, dest=0)
                else:
                    comm.send(0, dest=0)
                requested_file = comm.recv(source=0)
                if requested_file in server_file_contents:
                    comm.send(rank, dest=0)
                else:
                    comm.send(0, dest=0)
                total = total_size(server_file_contents)
                comm.send(total, dest=0)
                file_content = comm.recv(source=0)
                file_name = comm.recv(source=0)
                if len(file_name) == 0:
                    continue
                else:
                    file_path = os.path.join(SERVER_DIRECTORY, file_name)
                    with open(file_path, "wb") as file:
                        file.write(file_content)
            elif trigger == "-m":
                load_server_file_contents(SERVER_DIRECTORY)
                requested_file = comm.recv(source=0)
                if requested_file in server_file_contents:
                    meta = get_meta(SERVER_DIRECTORY, requested_file)
                    comm.send(meta, dest=0)
    else:
        for i in range(1,size):
            server_file_contents[i] = (comm.recv(source=i))
        threads = []
        thread = threading.Thread(target=start_server, args=(PORT,))
        threads.append(thread)
        thread.start()

        for thread in threads:
            thread.join()

if __name__ == "__main__":
    main()