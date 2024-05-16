from pathlib import Path

from socketwrench.tags import private, post, put, patch, delete, route, methods


def hello():
    """A simple hello world function."""
    return "world"


@methods("GET", "POST")  # do to the label, this will be accessible by both GET and POST requests
def hello2(method):
    """A simple hello world function."""
    return "world"


def _unserved():
    """This function will not be served."""
    return "this will not be served"


@private
def unserved():
    """This function will not be served."""
    return "this will not be served"


@post
def post(name):
    """This function will only be served by POST requests."""
    return f"hello {name}"


@put
def put(name):
    """This function will only be served by PUT requests."""
    return f"hello {name}"


@patch
def patch(name):
    """This function will only be served by PATCH requests."""
    return f"hello {name}"


@delete
def delete(name):
    """This function will only be served by DELETE requests."""
    return f"hello {name}"


def echo(*args, **kwargs):
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


def string() -> str:
    """Returns a string response."""
    return "this is a string"


def html() -> str:
    """Returns an HTML response."""
    return "<h1>hello world</h1><br><p>this is a paragraph</p>"


def json() -> dict:
    """Returns a JSON response."""
    return {"x": 6, "y": 7}


def file() -> Path:
    """Returns sample.py as a file response."""
    return Path(__file__)


def add(x: int, y: int):
    """Adds two numbers together."""
    return x + y


def client_addr(client_addr):
    """Returns the client address."""
    return client_addr


def headers(headers) -> dict:
    """Returns the request headers."""
    return headers


def query(query, *args, **kwargs) -> str:
    """Returns the query string."""
    return query


def body(body) -> bytes:
    """Returns the request body."""
    return body


def method(method) -> str:
    """Returns the method."""
    return method




def request(request) -> dict:
    """Returns the request object."""
    return request


def everything(request, client_addr, headers, query, body, method, route, full_path):
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
def a(b, c=5):
    print(f"calling a with b={b}, c={c}")
    return f"captured b={b}, c={c}"


if __name__ == '__main__':
    import logging
    from socketwrench import serve

    logging.basicConfig(level=logging.DEBUG)
    # SocketWrench.serve_module("socketwrench.samples.file_sample")
    # OR
    serve(__file__)