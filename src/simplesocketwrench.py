import socket
import logging


class Server:
    def __init__(self, port: int = 8080, host: str = '', logger: logging.Logger | str | None = None):
        self.host = host
        self.port = port
        self._log = logger if isinstance(logger, logging.Logger) else logging.getLogger(logger if logger else self.__class__.__name__)

        self.server_socket = self.create_socket()

    def create_socket(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(1)
        return self.server_socket

    def serve(self):
        self._log.info(f'Serving HTTP on port {self.port}...')
        while True:
            client_connection, client_address = self.server_socket.accept()
            request = self.receive_request(client_connection)
            response = self.handle_request(request)
            self.send_response(client_connection, response)

    def receive_request(self, client_connection: socket.socket) -> str:
        request_data = b''
        while True:
            chunk = client_connection.recv(1024)
            request_data += chunk
            if chunk.endswith(b'\r\n\r\n'):
                break

        # Parsing Content-Length if present for requests with body
        headers = request_data.split(b'\r\n\r\n')[0]
        if b'Content-Length:' in headers:
            length = int(headers.split(b'Content-Length: ')[1].split(b'\r\n')[0])
            while len(request_data) < length + len(headers) + 4:  # 4 for the two CRLFs
                request_data += client_connection.recv(1024)

        return request_data.decode()

    def handle_request(self, request: str) -> str:
        self._log.debug(f'Handling request: {request}')
        response = 'HTTP/1.0 200 OK\n\nOK'
        return response

    def send_response(self, client_connection: socket.socket, response: str):
        client_connection.sendall(response.encode())
        client_connection.close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    Server().serve()
