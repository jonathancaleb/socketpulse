import logging
from pathlib import Path

import cv2
import numpy as np

from socketpulse.handlers import StaticFileHandler
from socketpulse.tags import private, post, put, patch, delete, route, methods
from socketpulse.types import TBDBResponse, FileTypeResponse

logging.basicConfig(level=logging.DEBUG)


class Sample:
    src = StaticFileHandler(Path(__file__).parent.parent.parent)

    def hello(self):
        """A simple hello world function."""
        return "world"

    @methods("GET", "POST")  # do to the label, this will be accessible by both GET and POST requests
    def hello2(self, method):
        """A simple hello world function."""
        return "world"

    def _unserved(self):
        """This function will not be served."""
        return "this will not be served"

    @private
    def unserved(self):
        """This function will not be served."""
        return "this will not be served"

    @post
    def post(self, name):
        """This function will only be served by POST requests."""
        return f"hello {name}"

    @put
    def put(self, name):
        """This function will only be served by PUT requests."""
        return f"hello {name}"

    @patch
    def patch(self, name):
        """This function will only be served by PATCH requests."""
        return f"hello {name}"

    @delete
    def delete(self, name):
        """This function will only be served by DELETE requests."""
        return f"hello {name}"

    def echo(self, *args, **kwargs):
        """Echos back any query or body parameters."""
        if not args and not kwargs:
            return
        if args:
            if len(args) == 1:
                return args[0]
            return args
        elif kwargs:
            return kwargs
        return args, kwargs

    def string(self) -> str:
        """Returns a string response."""
        return "this is a string"

    def html(self) -> str:
        """Returns an HTML response."""
        return "<h1>hello world</h1><br><p>this is a paragraph</p>"

    def json(self) -> dict:
        """Returns a JSON response."""
        return {"x": 6, "y": 7}

    def file(self) -> Path:
        """Returns sample.py as a file response."""
        return Path(__file__)

    def add(self, x: int, y: int):
        """Adds two numbers together."""
        return x + y

    def client_addr(self, client_addr):
        """Returns the client address."""
        return client_addr

    def headers(self, headers) -> dict:
        """Returns the request headers."""
        return headers

    def query(self, query, *args, **kwargs) -> str:
        """Returns the query string."""
        return query

    def body(self, body) -> bytes:
        """Returns the request body."""
        return body

    def method(self, method) -> str:
        """Returns the method."""
        return method

    def get_route(self, route) -> str:
        """Returns the route."""
        return route

    def request(self, request) -> dict:
        """Returns the request object."""
        return request

    def everything(self, request, client_addr, headers, query, body, method, route, full_path):
        d = {
            "request": request,
            "client_addr": client_addr,
            "headers": headers,
            "query": query,
            "body": body,
            "method": method,
            "route": route,
            "full_path": full_path,
        }
        for k, v in d.items():
            print(k, v)
        return d

    @route("/a/{c}", error_mode="traceback")
    def a(self, b, c=5):
        print(f"calling a with b={b}, c={c}")
        return f"captured b={b}, c={c}"


    @route("{misc}")
    def misc(self, misc):
        return f"misc={misc}"

    @route("/a/{b}_is1/c/{d}_is1")
    def a_c1(self, b, d):
        return f"a_c1: b={b}, d={d}"

    @route("/a/{b}/c/{d}")
    def a_c(self, b, d, socket=None):
        s = f"a_c: b={b}, d={d}, socket={str(socket)}".replace("<", "&lt").replace(">", "&gt")
        return s

    @route("/a/{b}_is2/c/{d}_is2")
    def a_c2(self, b, d):
        return f"a_c2: b={b}, d={d}"

    @route("/a/{b}_is2/c/{d}_is{e}")
    def a_c3(self, b, d, e):
        return f"a_c3: b={b}, d={d}, e={e}"

    def tbdb_test(self) -> TBDBResponse:
        return [
            {"x": 6, "y": 7, "z": 8},
            {"x": 22, "y": 33, "z": 44},
            {"x": 55, "y": 66, "z": 77},
        ]

    def random_img(self) -> FileTypeResponse("image/png", lambda x: cv2.imencode(".png", x.astype(np.uint8))[1].tobytes()):
        x = np.random.rand(100, 100, 3) * 255
        x = x.astype(np.uint8)
        return x


if __name__ == '__main__':
    from socketpulse import serve
    s = Sample()
    serve(s)
    # OR
    # serve(Sample)
    # OR
    # serve("socketpulse.samples.sample.Sample")
