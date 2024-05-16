# How to make a webserver with python
## Introduction
HTTP web requests are actually quite simple, at least when you are just looking at the protocol and the data sent in the requests, and not worrying about the mechanisms of HOW the requests are sent.
The basic idea is that the client sends a bytes-encoded text string "request" to the server, and the server sends a bytes-encoded text string "response" back to the client.

```
{method} {path} {version}
{headerKey1}: {headerValue1}
{headerKey2}: {headerValue2}
...

{body}
```

- The request line, which contains the method, the path, and the HTTP version
  - The method is one of the following: `GET`, `POST`, `PUT`, `DELETE`, `HEAD`, `OPTIONS`, `CONNECT`, `TRACE`
  - The path is the path to the resource on the server, e.g. `/index.html`
  - The HTTP version is the version of the HTTP protocol being used, e.g. `HTTP/1.1`
- The headers
    - Headers are key-value pairs that contain metadata about the request, all keys and values are strings
    - Each key-value pair is on a new line and key:values are separated by a colon `:`
    - Some common headers are `Content-Type`, `Content-Length`, `User-Agent`, `Host`, `Accept`, `Accept-Encoding`, `Accept-Language`, `Connection`, `Cookie`, `Date`, `Referer`, `Server`, `Set-Cookie`, `Transfer-Encoding`, `Upgrade`, `Via`, `Warning`
    - headers are separated from the body by a blank line
- The body

For example, when you visit google.com, the simplest request you could send would look like this:
`GET / HTTP/1.1`

A slightly more complex request would look like this:
```
GET /some/path?search=x&param=y#hash HTTP/1.1
Host: www.google.com
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3
```

To which the server might respond with some HTML, which would look like this:
```
HTTP/1.1 200 OK
Content-Type: text/html

<!DOCTYPE html>
<html>
<head>
    <title>Google</title>
</head>
<body>
    <h1>Google</h1>
    <p>Search the web</p>
</body>
</html>
```

And a POST request to upload a small file would look like this:
```
POST /upload_my_file HTTP/1.1
Host: www.example.com
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3
Content-Disposition: form-data; name="file"; filename="example.txt"
Content-Type: text/plain

This is the content of the file
```

The server then sends a response back to the client, which looks like this:
```
HTTP/1.1 200 OK
```

## Making a web server
Python offers lots of pre-built well-tested webservers, such as Flask, Django, and FastAPI, but if you want to learn how to make a webserver from scratch, you can use the built-in `socket` module.

In [simplestsocketwrench.py](./src/simplestsocketwrench.py), we create a simple webserver that listens on port 8080 and responds to any request with a simple HTML page.

```python
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
```

It is really that simple! if you run this script and go to `http://localhost:8080` in your browser, you will see the text "OK" displayed on the page.


If you understand [simplestsocketwrench.py](./src/simplestsocketwrench.py), you can move on to [simplesocketwrench.py](./src/simplesocketwrench.py), which is a slightly more organized version of the same script that uses classes and methods to handle requests.

[simplesocketwrench.py](./src/simplesocketwrench.py) is probably the place to start if you want to buil an ultra-lean webserver from scratch.
`socketwrench` has a few more layers of abstraction and ease-of-use features that make it easier to use (hopefully) but harder to understand. 
It still has nowhere near the complexity or the amount of features of Flask or Tornado, with the upside being it is small and lightweight.





