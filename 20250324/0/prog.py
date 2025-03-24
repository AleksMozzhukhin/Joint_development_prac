import sys
import socket
from http.server import SimpleHTTPRequestHandler, HTTPServer


def test(HandlerClass=SimpleHTTPRequestHandler,
         ServerClass=HTTPServer,
         protocol="HTTP/1.0", port=8000, bind=""):
    if not bind:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            bind = s.getsockname()[0]
        except Exception as e:
            print("Ошибка определения локального IP:", e)
            bind = '127.0.0.1'
        finally:
            s.close()

    server_address = (bind, port)
    HandlerClass.protocol_version = protocol
    httpd = ServerClass(server_address, HandlerClass)
    sa = httpd.socket.getsockname()
    print("Serving HTTP on {} port {} ...".format(sa[0], sa[1]))
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received, exiting.")
        httpd.server_close()


if __name__ == '__main__':
    try:
        port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    except ValueError:
        print("Порт должен быть числом.")
        sys.exit(1)
    test(port=port)
