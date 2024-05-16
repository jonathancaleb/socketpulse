import dataclasses
import datetime
import json
import socket
from pathlib import Path


class HTTPVersion(str):
    """Represents an HTTP version string."""
    HTTP_0_9 = "HTTP/0.9"
    HTTP_1_0 = "HTTP/1.0"
    HTTP_1_1 = "HTTP/1.1"
    HTTP_2_0 = "HTTP/2.0"
    HTTP_3_0 = "HTTP/3.0"


class HTTPMethod(str):
    """Represents an HTTP method string."""
    GET = "GET"
    HEAD = "HEAD"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    CONNECT = "CONNECT"
    OPTIONS = "OPTIONS"
    TRACE = "TRACE"
    PATCH = "PATCH"

class Body(bytes):
    EMPTY = b""

class RequestBody(Body):
    pass


class Headers(dict):
    EMPTY = {}

    def to_string(self) -> str:
        s = ""
        for k, v in self.items():
            s += f"{k}: {v}\n"
        return s

    def __str__(self):
        return self.to_string()

    def to_bytes(self) -> bytes:
        return self.to_string().encode()


class HeaderBytes(bytes):
    EMPTY = b""

    def __new__(cls, s: bytes | Headers | dict[str, str]):
        if isinstance(s, Headers):
            s = s.to_bytes()
        elif isinstance(s, dict):
            s = Headers(s).to_bytes()
        return super().__new__(cls, s)

    def to_string(self):
        return self.decode()

    def to_dict(self) -> dict:
        lines = self.decode().splitlines()
        items = [v.split(":", 1) for v in lines]
        d = {k.strip(): v.strip() for k, v in items}
        return Headers(d)

    def __iter__(self):
        return iter(self.to_dict())


class RequestPath(str):
    EMPTY = ""
    BASE = "/"

    def query(self) -> str:
        """Extracts the query string from the path."""
        if "?" not in self:
            return ""
        q = self.split("?", 1)[1]
        return q

    def route(self) -> str:
        """Extracts the path from the path and remove the query."""
        p = self.split("?", 1)[0]
        return p

    def query_args(self) -> dict[str, str]:
        """Extracts the query string from the path and parses into a dictionary."""
        q = self.query()
        if not q:
            return {}
        items = [v.split("=", 1) for v in q.split("&")]
        d = {url_decode(k): url_decode(v) for k, v in items}
        return d


class ClientAddr(str):
    def __new__(cls, host_port: str | tuple[str, int]):
        if isinstance(host_port, tuple):
            host = host_port[0]
            port = host_port[1]
        else:
            host = host_port
            port = None
        self = super().__new__(cls, host)
        self.host = host
        self.port = port
        return self


class Request:
    @classmethod
    def from_components(cls, pre_body_bytes: bytes, body: bytes, client_addr: str | tuple[str, int], connection_socket: socket.socket = None) -> "Request":
        """Create a Request object from a header string and a body bytes object."""
        i = pre_body_bytes.index(b"\r\n")
        first_line = pre_body_bytes[:i].decode()
        method, path, version = first_line.split(" ")
        header_bytes = pre_body_bytes[i + 2:]
        return cls(method, path, version, header_bytes, body, client_addr, connection_socket)

    def __init__(self,
                 method: str | HTTPMethod = HTTPMethod.GET,
                 path: str | RequestPath = RequestPath.BASE,
                 version: str | HTTPVersion = HTTPVersion.HTTP_1_1,
                 header: bytes | HeaderBytes | Headers | dict[str, str] = HeaderBytes.EMPTY,
                 body: bytes | RequestBody = RequestBody.EMPTY,
                 client_addr: str | tuple[str, int] | None = None,
                 connection_socket: socket.socket | None = None
                 ):
        self.method = HTTPMethod(method)
        self.path = RequestPath(path)
        self.version = HTTPVersion(version)
        self.header_bytes = HeaderBytes(header)
        self._headers = None
        self.body = RequestBody(body)
        self.client_addr = ClientAddr(client_addr) if client_addr else None
        self.connection_socket = connection_socket

    @property
    def headers(self) -> Headers:
        if self._headers is None:
            self._headers = Headers(self.header_bytes.to_dict())
        return self._headers

    def to_string(self) -> str:
        return f'{self.method} {self.path} {self.version}\r\n{self.headers}\r\n\r\n{self.body}'

    def to_json(self) -> str:
        return json.dumps({
            "method": self.method,
            "path": self.path,
            "version": self.version,
            "headers": self.headers,
            "body": str(self.body),
            "client_addr": self.client_addr
        })

    def __repr__(self):
        return f"<Request {self.method} {self.path} client_addr={self.client_addr} ...>"


class ResponseBody(Body):
    pass


class HTTPStatusCode(int):
    # Informational Responses
    CONTINUE = 100
    SWITCHING_PROTOCOLS = 101
    PROCESSING = 102
    EARLY_HINTS = 103

    # Successful Responses
    OK = 200
    CREATED = 201
    ACCEPTED = 202
    NON_AUTHORITATIVE_INFORMATION = 203
    NO_CONTENT = 204
    RESET_CONTENT = 205
    PARTIAL_CONTENT = 206
    MULTI_STATUS = 207
    ALREADY_REPORTED = 208
    IM_USED = 226

    # Redirection Messages
    MULTIPLE_CHOICES = 300
    MOVED_PERMANENTLY = 301
    FOUND = 302
    SEE_OTHER = 303
    NOT_MODIFIED = 304
    USE_PROXY = 305
    TEMPORARY_REDIRECT = 307
    PERMANENT_REDIRECT = 308

    # Client Error Responses
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    PAYMENT_REQUIRED = 402
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    NOT_ACCEPTABLE = 406
    PROXY_AUTHENTICATION_REQUIRED = 407
    REQUEST_TIMEOUT = 408
    CONFLICT = 409
    GONE = 410
    LENGTH_REQUIRED = 411
    PRECONDITION_FAILED = 412
    PAYLOAD_TOO_LARGE = 413
    URI_TOO_LONG = 414
    UNSUPPORTED_MEDIA_TYPE = 415
    RANGE_NOT_SATISFIABLE = 416
    EXPECTATION_FAILED = 417
    IM_A_TEAPOT = 418
    MISDIRECTED_REQUEST = 421
    UNPROCESSABLE_ENTITY = 422
    LOCKED = 423
    FAILED_DEPENDENCY = 424
    TOO_EARLY = 425
    UPGRADE_REQUIRED = 426
    PRECONDITION_REQUIRED = 428
    TOO_MANY_REQUESTS = 429
    REQUEST_HEADER_FIELDS_TOO_LARGE = 431
    UNAVAILABLE_FOR_LEGAL_REASONS = 451

    # Server Error Responses
    INTERNAL_SERVER_ERROR = 500
    NOT_IMPLEMENTED = 501
    BAD_GATEWAY = 502
    SERVICE_UNAVAILABLE = 503
    GATEWAY_TIMEOUT = 504
    HTTP_VERSION_NOT_SUPPORTED = 505
    VARIANT_ALSO_NEGOTIATES = 506
    INSUFFICIENT_STORAGE = 507
    LOOP_DETECTED = 508
    NOT_EXTENDED = 510
    NETWORK_AUTHENTICATION_REQUIRED = 511

    def __new__(cls, status_code: int, phrase: str | None = None):
        self = super().__new__(cls, status_code)
        self._phrase = phrase
        return self

    def phrase(self) -> str:
        if self._phrase is None:
            for k, v in self.__class__.__dict__.items():
                if v == self:
                    self._phrase = k.replace("_", " ")
                    break
            else:
                self._phrase = "Unknown"
        return self._phrase

    def is_informational(self) -> bool:
        return 100 <= self <= 199

    def is_successful(self) -> bool:
        return 200 <= self <= 299

    def is_redirect(self) -> bool:
        return 300 <= self <= 399

    def is_client_error(self) -> bool:
        return 400 <= self <= 499

    def is_server_error(self) -> bool:
        return 500 <= self <= 599

    def __str__(self) -> str:
        return f'{int(self)} {self.phrase()}'


for k, v in HTTPStatusCode.__dict__.items():
    if isinstance(v, int):
        setattr(HTTPStatusCode, k, HTTPStatusCode(v, k.replace("_", " ")))


class ResponseTypehint:
    def __init__(self, content_type: str):
        self.content_type = content_type


class ResponseType(type):
    def __getitem__(self, item):
        class TypedResponse(Response):
            default_content_type = item
        return TypedResponse


class Response(metaclass=ResponseType):
    default_content_type = None

    def __new__(cls, body: bytes | ResponseBody = ResponseBody.EMPTY,
                status_code: int | HTTPStatusCode = HTTPStatusCode.OK,
                headers: bytes | HeaderBytes | Headers | dict = HeaderBytes.EMPTY,
                version: str | HTTPVersion = HTTPVersion.HTTP_1_1,
                **headers_kwargs):
        # If the body is already a Response instance, return it
        if isinstance(body, Response):
            return body

        # Create an instance of the appropriate subclass based on the body type
        if cls is Response:
            if isinstance(body, (bytes, memoryview)):
                return super(Response, cls).__new__(cls)
            elif isinstance(body, str):
                return super(Response, HTMLResponse).__new__(HTMLResponse)
            elif isinstance(body, Path):
                return super(Response, FileResponse).__new__(FileResponse)
            elif isinstance(body, Exception):
                return super(Response, ErrorResponse).__new__(ErrorResponse)
            else:
                return super(Response, JSONResponse).__new__(JSONResponse)
        else:
            return super(Response, cls).__new__(cls)

    def __init__(self,
                 body: bytes | ResponseBody = ResponseBody.EMPTY,
                 status_code: int | HTTPStatusCode = HTTPStatusCode.OK,
                 headers: bytes | HeaderBytes | Headers | dict = HeaderBytes.EMPTY,
                 version: str | HTTPVersion = HTTPVersion.HTTP_1_1,
                 **headers_kwargs
                 ):
        self.status_code = HTTPStatusCode(status_code)
        self.version = HTTPVersion(version)
        self.header_bytes = HeaderBytes(headers)
        self.headers = Headers(self.header_bytes.to_dict())
        for k, v in headers_kwargs.items():
            t = k.replace("_", " ").title().replace(" ", "-")
            if not isinstance(v, str):
                v = json.dumps(v)
            self.headers[t] = v
        self.body = ResponseBody(body)

    def pre_body_bytes(self) -> bytes:
        return f'{self.version} {self.status_code}\r\n{self.headers}\r\n'.encode()

    def __repr__(self):
        return f"<Response {self.status_code} {self.body[:10]}>"

    def __bytes__(self):
        return self.pre_body_bytes() + self.body

    def __buffer__(self, flags):
        return memoryview(bytes(self))


class FileResponse(Response):
    content_types = {
        "html": "text/html",
        "css": "text/css",
        "js": "application/javascript",
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "gif": "image/gif",
        "svg": "image/svg+xml",
        "bmp": "image/bmp",
        "tiff": "image/tiff",
        "ico": "image/x-icon",
        "webp": "image/webp",
        "stl": "model/stl",
        "obj": "model/obj",
        "fbx": "model/fbx",
        "glb": "model/gltf-binary",
        "gltf": "model/gltf+json",
        "3ds": "model/3ds",
        "3mf": "model/3mf",
        "json": "application/json",
        "yml": "application/x-yaml",
        "yaml": "application/x-yaml",
        "doc": "application/msword",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "xls": "application/vnd.ms-excel",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "ppt": "application/vnd.ms-powerpoint",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "odt": "application/vnd.oasis.opendocument.text",
        "ods": "application/vnd.oasis.opendocument.spreadsheet",
        "odp": "application/vnd.oasis.opendocument.presentation",
        "odg": "application/vnd.oasis.opendocument.graphics",
        "odf": "application/vnd.oasis.opendocument.formula",
        "pdf": "application/pdf",
        "zip": "application/zip",
        "tar": "application/x-tar",
        "gz": "application/gzip",
        "mp3": "audio/mpeg",
        "mp4": "video/mp4",
        "webm": "video/webm",
        "ogg": "audio/ogg",
        "wav": "audio/wav",
        "txt": "text/plain",
        "csv": "text/csv",
        "xml": "text/xml",
        "md": "text/markdown",
        "py": "text/x-python",
        "c": "text/x-c",
        "cpp": "text/x-c++",
        "h": "text/x-c-header",
        "hs": "text/x-haskell",
        "java": "text/x-java",
        "sh": "text/x-shellscript",
        "bat": "text/x-batch",
        "ps1": "text/x-powershell",
        "rb": "text/x-ruby",
        "rs": "text/x-rust",
        "go": "text/x-go",
        "php": "text/x-php",
        "pl": "text/x-perl",
        "swift": "text/x-swift",
        "asm": "text/x-asm",
        "toml": "application/toml",
        "ini": "text/x-ini",
        "cfg": "text/x-config",
        "conf": "text/x-config",
        "gitignore": "text/x-gitignore",
        "dockerfile": "text/x-dockerfile",
        None: "application/octet-stream"
    }

    default_content_type = None

    def __new__(cls, *args, **kwargs):
        return super().__new__(cls)

    def __init__(self,
                 *a,
                 body: bytes = b"",
                 path: str | Path = None,
                 filename: str | None = None,
                 extension: str | None = None,
                 status_code: int = 200,
                 headers: dict = None,
                 content_type: str | None = None,
                 download: bool = False,
                 version: str = "HTTP/1.1"):
        if content_type is None and self.default_content_type is not None:
            content_type = self.default_content_type
        if content_type is None and extension is not None:
            content_type = self.get_content_type(extension.lstrip("."))

        if a:
            if len(a) == 1:
                if isinstance(a[0], str):
                    if Path(a[0]).exists():
                        path = Path(a[0])
                    else:
                        body = a[0].encode()
                elif isinstance(a[0], Path):
                    path = a[0]
                else:
                    body = a[0]

        path = Path(path) if path else Path(".") if not body else None
        if filename is None:
            if path:
                filename = path.name
            elif extension:
                filename = "file." + extension.lstrip(".")
            elif content_type:
                filename = "file" + self.get_extension(content_type)
            else:
                filename = "file"
        if path and body:
            raise ValueError(f"Cannot have both a path and data: {path}, {body}")
        if not path and not body:
            raise ValueError("Must have either a path or data.")
        if body:
            if isinstance(body, str):
                body = body.encode()
            elif isinstance(body, bytes):
                pass
            elif isinstance(a[0], (bytearray, memoryview)):
                body = bytes(a[0])
            elif hasattr(a[0], "read"):
                body = a[0].read()
            elif hasattr(a[0], "tobytes"):
                body = a[0].tobytes()
            elif hasattr(a[0], "to_bytes"):
                body = a[0].to_bytes()
            elif hasattr(a[0], "dumps"):
                body = (a[0]).dumps().encode()
            elif isinstance(a[0], dict):
                body = json.dumps(a[0]).encode()
            else:
                raise ValueError(f"Invalid argument: {a[0]}")

        if headers is None:
            headers = {}

        if download and "Content-Disposition" not in headers:
            headers["Content-Disposition"] = f'attachment; filename="{filename}"'

        # add headers related to file stats
        if "Content-Length" not in headers:
            headers["Content-Length"] = str(path.stat().st_size) if path else str(len(body))
        if "Last-Modified" not in headers:
            headers["Last-Modified"] = datetime.datetime.fromtimestamp(path.stat().st_mtime).isoformat() if path else datetime.datetime.now().isoformat()

        if path and path.is_dir():
            from tempfile import TemporaryFile
            from zipfile import ZipFile
            # zip the directory to a TemporaryFile
            with TemporaryFile() as f:
                with ZipFile(f, "w") as z:
                    for p in path.iterdir():
                        z.write(p, p.name)
                f.seek(0)
                super().__init__(f.read(),
                                 status_code=status_code,
                                 headers=headers,
                                 content_type="application/zip",
                                 version=version)
        elif path:
            if content_type is None:
                content_type = self.get_content_type(path.suffix[1:])

            if not path.exists():
                raise FileNotFoundError(f"No such file or directory: '{path}'")
            with path.open("rb") as f:
                f.seek(0)
                b = f.read()

            super().__init__(b,
                             status_code=status_code,
                             headers=headers,
                             content_type=content_type,
                             version=version)
        else:
            super().__init__(body,
                             status_code=status_code,
                             headers=headers,
                             content_type=content_type,
                             version=version)

    def get_content_type(self, suffix: str):
        return self.content_types.get(suffix.lower(), self.content_types[self.default_content_type])

    def get_extension(self, content_type: str):
        for k, v in self.content_types.items():
            if v == content_type:
                return "." + k
        return ""


# define a class such that FileTypeResponse[content_type] is a subclass of FileResponse


class FileTypeResponseMeta(type):
    def __getitem__(self, content_type):
        return self.get_class(content_type)

    @classmethod
    def get_class(cls, content_type, write_function=None):
        # Create a new subclass of FileResponse with a custom content type
        if content_type[0] == "." and content_type[1:] in FileResponse.content_types:
            content_type = FileResponse.content_types[content_type[1:]]

        class TypedFileResponse(FileResponse):
            default_content_type = content_type

            def __init__(self,
                         *a,
                         body: bytes = b"",
                         path: str | Path = None,
                         filename: str | None = None,
                         extension: str | None = None,
                         status_code: int = 200,
                         headers: dict = None,
                         content_type: str | None = None,
                         download: bool = False,
                         version: str = "HTTP/1.1"):
                if write_function:
                    r = write_function(*a)
                    a = (r,)
                super().__init__(*a,
                                    body=body,
                                    path=path,
                                    filename=filename,
                                    extension=extension,
                                    status_code=status_code,
                                    headers=headers,
                                    content_type=content_type,
                                    download=download,
                                    version=version)


        # Generate a class name based on the content type
        ct_name = content_type.split("/")[-1].replace(".", "").replace("-", "").upper()
        TypedFileResponse.__name__ = f"{ct_name}FileResponse"

        return TypedFileResponse

    def __subclasscheck__(self, subclass):
        return issubclass(subclass, FileResponse)


class FileTypeResponse(metaclass=FileTypeResponseMeta):
    def __new__(cls, *args, **kwargs):
        return FileTypeResponseMeta.get_class(*args, **kwargs)


class HTMLResponse(Response):
    def __init__(self, html: str, status_code: int = 200, headers: dict = None, version: str = "HTTP/1.1"):
        if headers is None:
            headers = {}
        if "Content-Type" not in headers:
            headers["Content-Type"] = "text/html"
        Response.__init__(self, html.encode(), status_code, headers, version)


class StandardHTMLResponse(HTMLResponse):
    def __init__(self, body: str, title = "", favicon=None,  scripts: list = None, stylesheets = None, status_code: int = 200, headers: dict = None, version: str = "HTTP/1.1"):
        favicon = f'<link rel="icon" href="{favicon}">' if favicon else ""
        scripts = "\n".join([f'<script src="{i}"></script>' for i in scripts]) if scripts else ""
        stylesheets = "\n".join([f'<link rel="stylesheet" href="{i}">' for i in stylesheets]) if stylesheets else ""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    {favicon}
    {scripts}
    {stylesheets}
</head>
<body>
    {body}
</body>
</html>"""
        super().__init__(html, status_code, headers, version)


class HTMLTextResponse(StandardHTMLResponse): # this is easier to implement than escaping the text
    def __init__(self, body: str, title="", favicon=None,  scripts: list = None, stylesheets = None, status_code: int = 200, headers: dict = None, version: str = "HTTP/1.1"):
        super().__init__(f"<pre>{body}</pre>",
                            title=title,
                            favicon=favicon,
                            scripts=scripts,
                            stylesheets=stylesheets,
                            status_code=status_code,
                            headers=headers,
                            version=version)


class TBDBResponse(StandardHTMLResponse):
    """Displays tabular json data in a table using https://github.com/modularizer/teebydeeby"""
    def __init__(self, data, title="", favicon=None,  scripts: list = None, stylesheets = None, status_code: int = 200, headers: dict = None, version: str = "HTTP/1.1"):
        if not isinstance(data, str):
            data = json.dumps(data, indent=4)
        super().__init__(f"<teeby-deeby>{data}</teeby-deeby>",
                            title=title,
                            favicon=favicon,
                            scripts=["https://cdnjs.cloudflare.com/ajax/libs/lz-string/1.4.4/lz-string.min.js", "https://modularizer.github.io/teebydeeby/tbdb.js"] + list(scripts or []),
                            stylesheets=stylesheets,
                            status_code=status_code,
                            headers=headers,
                            version=version)



class JSONResponse(Response):
    def __init__(self, data: str | dict | list | tuple | int | float, status_code: int = 200, headers: dict = None,
                 version: str = "HTTP/1.1"):
        if headers is None:
            headers = {}
        if "Content-Type" not in headers:
            headers["Content-Type"] = "application/json"
        if not isinstance(data, str):
            if isinstance(data, tuple):
                data = list(data)
            if dataclasses.is_dataclass(data):
                data = dataclasses.asdict(data)

            if hasattr(data, "to_json"):
                try:
                    data = data.to_json()
                except:
                    if hasattr(data, "to_dict"):
                        try:
                            data = json.dumps(data.to_dict())
                        except:
                            data = str(data)
                    else:
                        data = str(data)
            elif hasattr(data, "to_dict"):
                try:
                    data = json.dumps(data.to_dict())
                except:
                    data = str(data)
            else:
                try:
                    data = json.dumps(data)
                except:
                    data = str(data)
        super().__init__(data.encode(), status_code, headers, version)


class ErrorResponse(Response):
    def __init__(self,
                 error: str | bytes | Exception = b'Internal Server Error',
                 status_code: int = 500,
                 headers: dict = None,
                 version: str = "HTTP/1.1"):
        if headers is None:
            headers = {}
        if isinstance(error, Exception):
            error = str(error).encode()
        elif isinstance(error, bytes):
            pass
        else:
            error = str(error).encode()
        if "Content-Type" not in headers:
            headers["Content-Type"] = "text/plain"
        super().__init__(error, status_code, headers, version)


class RedirectResponse(Response):
    def __init__(self, location: str, status_code: int = 307, headers: dict = None, version: str = "HTTP/1.1"):
        if headers is None:
            headers = {}
        if "Location" not in headers:
            headers["Location"] = location
        super().__init__(b"", status_code, headers, version)


class TemporaryRedirect(RedirectResponse):
    def __init__(self, location: str, status_code: int = 307, headers: dict = None, version: str = "HTTP/1.1"):
        super().__init__(location, status_code, headers, version)


class PermanentRedirect(RedirectResponse):
    def __init__(self, location: str, status_code: int = 308, headers: dict = None, version: str = "HTTP/1.1"):
        super().__init__(location, status_code, headers, version)


url_encodings = {
    " ": "%20",
    "!": "%21",
    '"': "%22",
    "#": "%23",
    "$": "%24",
    "%": "%25",
    "&": "%26",
    "'": "%27",
    "(": "%28",
    ")": "%29",
    "*": "%2A",
    "+": "%2B",
    ",": "%2C",
    "-": "%2D",
    ".": "%2E",
    "/": "%2F",
    "0": "%30",
    "1": "%31",
    "2": "%32",
    "3": "%33",
    "4": "%34",
    "5": "%35",
    "6": "%36",
    "7": "%37",
    "8": "%38",
    "9": "%39",
    ":": "%3A",
    ";": "%3B",
    "<": "%3C",
    "=": "%3D",
    ">": "%3E",
    "?": "%3F",
    "@": "%40",
    "A": "%41",
    "B": "%42",
    "C": "%43",
    "D": "%44",
    "E": "%45",
    "F": "%46",
    "G": "%47",
    "H": "%48",
    "I": "%49",
    "J": "%4A",
    "K": "%4B",
    "L": "%4C",
    "M": "%4D",
    "N": "%4E",
    "O": "%4F",
    "P": "%50",
    "Q": "%51",
    "R": "%52",
    "S": "%53",
    "T": "%54",
    "U": "%55",
    "V": "%56",
    "W": "%57",
    "X": "%58",
    "Y": "%59",
    "Z": "%5A",
    "[": "%5B",
    "\\": "%5C",
    "]": "%5D",
    "^": "%5E",
    "_": "%5F",
    "`": "%60",
    "a": "%61",
    "b": "%62",
    "c": "%63",
    "d": "%64",
    "e": "%65",
    "f": "%66",
    "g": "%67",
    "h": "%68",
    "i": "%69",
    "j": "%6A",
    "k": "%6B",
    "l": "%6C",
    "m": "%6D",
    "n": "%6E",
    "o": "%6F",
    "p": "%70",
    "q": "%71",
    "r": "%72",
    "s": "%73",
    "t": "%74",
    "u": "%75",
    "v": "%76",
    "w": "%77",
    "x": "%78",
    "y": "%79",
    "z": "%7A",
    "{": "%7B",
    "|": "%7C",
    "}": "%7D",
    "~": "%7E",
    "\x7F": "%7F",
    "€": "%E2%82%AC",
    "\x81": "%81",
    "‚": "%E2%80%9A",
    "ƒ": "%C6%92",
    "„": "%E2%80%9E",
    "…": "%E2%80%A6",
    "†": "%E2%80%A0",
    "‡": "%E2%80%A1",
    "ˆ": "%CB%86",
    "‰": "%E2%80%B0",
    "Š": "%C5%A0",
    "‹": "%E2%80%B9",
    "Œ": "%C5%92",
    "\x8D": "%C5%8D",
    "Ž": "%C5%BD",
    "\x8F": "%8F",
    "\x90": "%C2%90",
    "‘": "%E2%80%98",
    "’": "%E2%80%99",
    "“": "%E2%80%9C",
    "”": "%E2%80%9D",
    "•": "%E2%80%A2",
    "–": "%E2%80%93",
    "—": "%E2%80%94",
    "˜": "%CB%9C",
    "™": "%E2%84%A2",
    "š": "%C5%A1",
    "›": "%E2%80%BA",
    "œ": "%C5%93",
    "\x9D": "%9D",
    "ž": "%C5%BE",
    "Ÿ": "%C5%B8",
    "\xA0": "%C2%A0",
    "¡": "%C2%A1",
    "¢": "%C2%A2",
    "£": "%C2%A3",
    "¤": "%C2%A4",
    "¥": "%C2%A5",
    "¦": "%C2%A6",
    "§": "%C2%A7",
    "¨": "%C2%A8",
    "©": "%C2%A9",
    "ª": "%C2%AA",
    "«": "%C2%AB",
    "¬": "%C2%AC",
    "\xAD": "%C2%AD",
    "®": "%C2%AE",
    "¯": "%C2%AF",
    "°": "%C2%B0",
    "±": "%C2%B1",
    "²": "%C2%B2",
    "³": "%C2%B3",
    "´": "%C2%B4",
    "µ": "%C2%B5",
    "¶": "%C2%B6",
    "·": "%C2%B7",
    "¸": "%C2%B8",
    "¹": "%C2%B9",
    "º": "%C2%BA",
    "»": "%C2%BB",
    "¼": "%C2%BC",
    "½": "%C2%BD",
    "¾": "%C2%BE",
    "¿": "%C2%BF",
    "À": "%C3%80",
    "Á": "%C3%81",
    "Â": "%C3%82",
    "Ã": "%C3%83",
    "Ä": "%C3%84",
    "Å": "%C3%85",
    "Æ": "%C3%86",
    "Ç": "%C3%87",
    "È": "%C3%88",
    "É": "%C3%89",
    "Ê": "%C3%8A",
    "Ë": "%C3%8B",
    "Ì": "%C3%8C",
    "Í": "%C3%8D",
    "Î": "%C3%8E",
    "Ï": "%C3%8F",
    "Ð": "%C3%90",
    "Ñ": "%C3%91",
    "Ò": "%C3%92",
    "Ó": "%C3%93",
    "Ô": "%C3%94",
    "Õ": "%C3%95",
    "Ö": "%C3%96",
    "×": "%C3%97",
    "Ø": "%C3%98",
    "Ù": "%C3%99",
    "Ú": "%C3%9A",
    "Û": "%C3%9B",
    "Ü": "%C3%9C",
    "Ý": "%C3%9D",
    "Þ": "%C3%9E",
    "ß": "%C3%9F",
    "à": "%C3%A0",
    "á": "%C3%A1",
    "â": "%C3%A2",
    "ã": "%C3%A3",
    "ä": "%C3%A4",
    "å": "%C3%A5",
    "æ": "%C3%A6",
    "ç": "%C3%A7",
    "è": "%C3%A8",
    "é": "%C3%A9",
    "ê": "%C3%AA",
    "ë": "%C3%AB",
    "ì": "%C3%AC",
    "í": "%C3%AD",
    "î": "%C3%AE",
    "ï": "%C3%AF",
    "ð": "%C3%B0",
    "ñ": "%C3%B1",
    "ò": "%C3%B2",
    "ó": "%C3%B3",
    "ô": "%C3%B4",
    "õ": "%C3%B5",
    "ö": "%C3%B6",
    "÷": "%C3%B7",
    "ø": "%C3%B8",
    "ù": "%C3%B9",
    "ú": "%C3%BA",
    "û": "%C3%BB",
    "ü": "%C3%BC",
    "ý": "%C3%BD",
    "þ": "%C3%BE",
    "ÿ": "%C3%BF"
}


def url_encode(s: str) -> str:
    for k, e in url_encodings.items():
        s = s.replace(k, e)
    return s


def url_decode(s: str) -> str:
    for e, k in url_encodings.items():
        s = s.replace(k, e)
    return s


class Query(dict):
    def __str__(self):
        return "?" + "&".join([f"{url_encode(k)}={url_encode(v)}" for k, v in self.items()])


class Route(str):
    pass


class FullPath(str):
    pass


class Method(str):
    pass


class File(bytes):
    pass


class ErrorModes:
    HIDE = "hide"
    TYPE = "type"
    SHORT = "short"
    TRACEBACK = TB = LONG = SHOW = "traceback"

    DEFAULT = HIDE


def set_default_error_mode(mode: str):
    if mode not in [ErrorModes.HIDE, ErrorModes.TYPE, ErrorModes.SHORT, ErrorModes.TRACEBACK]:
        raise ValueError(f"Invalid error mode: {mode}. Options are 'hide', 'type', 'short', 'traceback'.")
    ErrorModes.DEFAULT = mode
