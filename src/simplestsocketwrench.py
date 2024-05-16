import socket

HOST = ""
PORT = 8080

# Create a socket object
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to the host and port
server_socket.bind((HOST, PORT))

# Enable the server to accept connections
server_socket.listen(1)

print(f'Serving HTTP on port {PORT}...')

while True:
    # Wait for an incoming connection
    client_connection, client_address = server_socket.accept()

    request_data = []
    while True:
        chunk = client_connection.recv(1024)
        request_data.append(chunk)
        if len(chunk) < 1024 or not chunk:
            break

    request = b''.join(request_data).decode()
    print(request)

    # Send HTTP response
    response = 'HTTP/1.0 200 OK\n\nOK'
    client_connection.sendall(response.encode())

    # Close the connection
    client_connection.close()
