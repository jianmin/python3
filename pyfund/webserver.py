"""A simple web server.

Usage:
    python webserver.py localhost 8080 /path/to/document/root
"""

import sys
import socket
import threading
import os.path

CRLFS = b"\r\n\r\n"

def get_usage():
    usage = """\
This script will start a web server

Usage: python webserver.py ip port /path/to/document/root
"""
    return usage

def firefox_not_supported():
    http_resp = b"""\
HTTP/1.1 200 OK
Content-Type: text/html; charset=UTF-8

<html>
<body>Firefox is not supported</body>
</html>
"""
    return http_resp

def response_not_supported():
    http_resp = b"""\
HTTP/1.1 200 OK
Content-Type: text/html; charset=UTF-8

<html>
<body>Content type not supported</body>
</html>
"""
    return http_resp

def response_404():
    http_resp = b"""\
HTTP/1.1 404 Not Found
Content-Type: text/html; charset=UTF-8

<html>
<body>404 File not found</body>
</html>
"""
    return http_resp

def get_content_type(uri):
    parts = uri.split(".")
    # -1 the last item in the list
    ext = parts[-1].lower()

    if (ext == "html" or ext == "htm"):
        return b"text/html; charset=UTF-8"
    elif (ext == "png"):
        return b"image/png"
    elif (ext == "jpeg" or ext == "jpg"):
        return b"image/jpeg"
    else:
        return None

def create_response_headers(content_type):
    headers = b"HTTP/1.1 200 OK\r\nContent-Type: " + content_type + b"\r\n\r\n"
    return headers

def read_request(client_sock):
    request_data = b""
    while True:
        request_data += client_sock.recv(4098)
        if len(request_data) == 0:
            break;
        if CRLFS in request_data:
            break

    method = None
    uri = None
    protocol = None
    headers = None
    body = None

    if len(request_data) == 0:
        # empty request
        return method, uri, protocol, headers, body

    parts = request_data.split(CRLFS, 1)
    header_lines = parts[0].decode("utf-8", "replace").split("\r\n")
    body = parts[1]
    headers = {}

    # Parse headers
    for header in header_lines:
        parts = header.split(":");
        length = len(parts)
        if (length == 1):
            # This is request line
            segments = header.split(" ");
            if (len(segments) == 3):
                method = segments[0];
                uri = segments[1];
                protocol = segments[2];
                if (uri == "/"):
                    uri = "/index.html"
        elif (length == 2):
            headers[parts[0]] = parts[1].strip()
        else:
            name = parts[0]
            headers[name] = parts[1].strip()
            for i in range(2, length):
                headers[name] += ":" + parts[i].strip()

    # Get the body length
    if "Content-Length" in headers: 
        blen = int(headers["Content-Length"]);
    else:
        blen = 0;

    # Read the body
    while len(body) < blen:
        body += client_sock.recv(4098)

    return method, uri, protocol, headers, body

def start_webserver(ip, port, docroot):
    listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listen_sock.bind((ip, port))
    listen_sock.listen(1)
    # 4 seconds accept timeout
    listen_sock.settimeout(4)

    print(f"Serving HTTP on port {port} ...")

    while True:
        try:
            # Wait for a connection...
            client_sock, client_addr = listen_sock.accept()
            if client_sock:
                print(f"HTTP server - accepted connection from {client_addr[0]}:{client_addr[1]}")
                method, uri, protocol, headers, body = read_request(client_sock)

                #print(headers);

                if method is None:
                    print("Empty request")
                    client_sock.close()
                    continue

                is_firefox = False;
                if "User-Agent" in headers: 
                    user_agent = headers["User-Agent"];
                    if "Firefox" in user_agent:
                        is_firefox = True

                if is_firefox is True:
                    client_sock.sendall(firefox_not_supported())
                else:
                    filename = docroot + uri

                    # Check whether the file exists
                    if os.path.isfile(filename):
                        content_type = get_content_type(uri)
                        if (content_type is None):
                            client_sock.sendall(response_not_supported())
                        else:
                            response_headers = create_response_headers(content_type)
                            client_sock.sendall(response_headers)
                            with open(filename, 'rb') as fh:
                                client_sock.send(fh.read())
                    else:
                        client_sock.sendall(response_404())
                # Close client socket
                client_sock.close()
                print("Client disconnected");
        except socket.timeout as e:
            print("HTTP server - timeout on accept")
    print("HTTP server - stopped")

def main(ip, port, docroot):
    start_webserver(ip, port, docroot)

if __name__ == "__main__":
    if ((len(sys.argv) < 4)):
        print(get_usage())
        sys.exit(1)
    else:
        main(sys.argv[1], int(sys.argv[2]), sys.argv[3])