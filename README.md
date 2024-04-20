# Distributed Filesystem using MPI and Socket

## Group 14

## April 20, 2024

## Design Explanation

This project implements a distributed filesystem using MPI (Message Passing  
Interface) for communication between nodes and sockets for communication  
between clients and the server. The system consists of multiple clients, a server,  
and multiple data nodes. Each client can upload, retrieve, list files, or get  
metadata for files.

- Clients (dfsclient.py): Clients interact with the server to perform file  
    operations. They can retrieve files, upload files, list files, or get metadata  
    for files.
- Server (dfsserver.py): The server listens for client connections and  
    handles their requests. It communicates with data nodes to perform file  
    operations such as storing and retrieving files.
- Data Nodes: Data nodes store files and handle file operations requested  
    by the server. They ensure data replication and efficient data distribution.
![[Pasted image 20240420175930.png]]
<p align="center">
Figure 1: System Architecture
</p>
## Building and Running

### Requirements

- Python 3.x
- MPI4py

To install MPI4py, you can use pip, the Python package manager. If you  
haven’t installed pip, you can download it from the official Python website  
(https://www.python.org/downloads/). Once pip is installed, you can in-  
stall MPI4py by running the following command in your terminal or command  
prompt:

```
1 pip install mpi4py
```

### Setup Server

- Run the server using MPI:  
    1 mpiexec -n 4 python dfs_server.py

### Running the Client

- To retrieve a file:  
    1 python dfs_client.py <file_name_in_the_database > -r
- To upload a file:  
    1 python dfs_client.py <file_name_from_client > -a
- To list all files from all servers: 
    1 python dfs_client.py list
- To get metadata of a file from the database:  
    1 python dfs_client.py <file_name_in_the_database > -m

### 2.4 Communication Flow

- Receive file:
    - The file name is sent from the client request to the server.
    - The server receives the file name and then broadcasts it to all MPI  
        processors.
    - Each processor loops through the file list of its corresponding data  
        node to find the requested file.
    - The MPI processor with the requested file sends the file and its con-  
        tent to the main server, which then sends it to the client.
- Upload file:
    - The file is sent from the client to the server.
    - The server receives the file and finds the data node with the  
        smallest data.
    - The server sends the file to the appropriate MPI processor and creates  
        a replicate file on another processor with the second smallest data.
    - If the file is already in the database, the file and its replicate will be  
        updated accordingly.
- Get meta:
    - The file name is sent to the server.
    - The server receives the file name and pushes it to all MPI processors.
    - Each processor loops through the file list of its corresponding data  
        node to find the requested file.
    - The MPI processor with the requested file sends the metadata of the  
        file to the main server, which then sends it to the client (encoded/de-  
        coded using pickle).
- Get list:
    - A signal ”list” is sent to the server.
    - The server gathers all file names from all MPI processors and sends  
        them to the client (encoded/decoded using pickle).

## 3 Scenario Demonstration

You can watch the demo of our project in the following video:
![[2024-04-20 14-00-07 1.mkv]]