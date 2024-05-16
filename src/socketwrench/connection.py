import socket
import logging

from socketwrench.types import Request, Response

logger = logging.getLogger("socketwrench")


class Connection:
    default_chunk_size: int = 1024

    def __init__(self,
                 handler,
                 connection_socket: socket.socket,
                 client_address: tuple,
                 cleanup_event,
                 chunk_size: int = default_chunk_size):
        self.socket = connection_socket
        self.client_addr = client_address
        self.chunk_size = chunk_size
        self.cleanup_event = cleanup_event
        self.handler = handler

        self._rep = None

    def handle(self):
        request = self.receive_request(self.socket)
        if self.check_cleanup():
            return request, None, False
        response = self.handler(request)
        if self.check_cleanup():
            return request, response, False
        self.send_response(self.socket, response)
        return request, response, True

    def receive_request(self, connection_socket: socket.socket, chunk_size: int = None) -> Request:
        if chunk_size is None:
            chunk_size = self.chunk_size

        new_line = b'\r\n'
        end_of_header = 2 * new_line

        request_data = b''
        while not self.cleanup_event or not self.cleanup_event.is_set():
            chunk = connection_socket.recv(chunk_size)
            request_data += chunk
            if end_of_header in request_data:
                break
            if not chunk:
                break

        # Extract headers
        pre_body_bytes, body = request_data.split(end_of_header, 1)

        # Parsing Content-Length if present for requests with body
        if b'Content-Length:' in pre_body_bytes:
            length = int(pre_body_bytes.split(b'Content-Length: ')[1].split(new_line)[0])
            while len(body) < length and not self.cleanup_event or not self.cleanup_event.is_set():
                body += connection_socket.recv(chunk_size)
        else:
            body = b''

        r = Request.from_components(pre_body_bytes, body, self.client_addr, self.socket)
        return r

    def send_response(self, connection_socket: socket.socket, response: Response):
        connection_socket.send(bytes(response))
        connection_socket.close()

    def check_cleanup(self):
        if self.cleanup_event and self.cleanup_event.is_set():
            self.close()
            return True
        return False

    def close(self):
        self.socket.close()

    def __repr__(self):
        if self._rep is None:
            r = ""
            if self.chunk_size != self.default_chunk_size:
                r += f", chunk_size={self.chunk_size}"

            self._rep = f'<{self.__class__.__name__}({self.socket}, {self.client_addr}, {self.cleanup_event}{r})>'
        return self._rep
