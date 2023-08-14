import argparse
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from inky.auto import auto
from PIL import Image, ImageOps
from ssl import PROTOCOL_TLS_SERVER, SSLContext
from utils import check_path, check_certificate
from os import walk
from urllib import parse

parser = argparse.ArgumentParser()

parser.add_argument("--host", default="0.0.0.0")
parser.add_argument("--port", default=8080)
parser.add_argument("--cert-file", default="cert.pem")
parser.add_argument("--private-key", default="private.key")
parser.add_argument("--uploads", default="uploads")

args = parser.parse_args()

#  check_socket(args.host, int(args.port))
check_certificate(args.cert_file, args.private_key)
check_path(args.uploads)


class BadgeServer(BaseHTTPRequestHandler):

    # curl -k -X GET https://raspberrypi.local:8080
    def do_GET(self):  # pylint: disable=invalid-name
        if self.path == "/":
            body = self._list_contents(args.uploads)
            self.send_response(200, "OK")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Content-Type", "application/json")
            self.end_headers()

            self.wfile.write(body.encode("utf-8"))
        else:
            self.send_response(404)

    @staticmethod
    def _list_contents(path: str):
        return json.dumps(next(walk(path), (None, None, []))[2])

    # curl -k -X DELETE https://raspberrypi.local/{basename}:8080
    def do_DELETE(self):  # pylint: disable=invalid-name
        filename = self._get_filename()

        if not os.path.exists(filename):
            self.send_response(404, "Not Found")
            self.end_headers()
            return

        os.remove(filename)

        self.send_response(204, "No Content")
        self.end_headers()

    def _get_filename(self):
        path = parse.urlparse(self.path).path
        basename = os.path.basename(path)
        return f"{args.uploads}/{basename}"

    # curl -k -X POST --upload-file {basename} https://raspberrypi.local:8080
    def do_POST(self):  # pylint: disable=invalid-name
        filename = self._get_filename()

        if os.path.exists(filename):
            self.send_response(409, "Conflict")
            self.end_headers()
            return

        with open(filename, "wb") as output:
            output.write(self.rfile.read(int(self.headers["Content-Length"])))

        self._set_image(filename)

        self.send_response(201, "Created")
        self.end_headers()

    # curl -k -X PUT https://raspberrypi.local/{basename}:8080
    def do_PUT(self):  # pylint: disable=invalid-name
        self._set_image(self._get_filename())
        self.send_response(202, "OK")
        self.end_headers()

    def _set_image(self, file):
        image = Image.open(file)

        params = parse.parse_qs(parse.urlparse(self.path).query)
        rotation = int(next(iter(params.get("rotation", [0]))))
        image = image.rotate(-rotation)

        inky = auto(ask_user=True, verbose=True)
        image = ImageOps.fit(image, inky.resolution)

        saturation = float(next(iter(params.get("saturation", [0.5]))))
        inky.set_image(image, saturation=saturation)
        inky.show()


if __name__ == "__main__":
    ssl_context = SSLContext(PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(args.cert_file, args.private_key)

    http_server = HTTPServer((args.host, int(args.port)), BadgeServer)
    print(f"Server started https://{args.host}:{args.port}")

    try:
        http_server.socket = ssl_context.wrap_socket(http_server.socket, server_side=True)
        http_server.serve_forever()
    except KeyboardInterrupt:
        pass

    http_server.server_close()
    print("Server stopped.")
