import argparse
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from os import walk

parser = argparse.ArgumentParser()

parser.add_argument("--host", default="localhost")
parser.add_argument("--port", default=8080)
parser.add_argument("--uploads", default="uploads")

args = parser.parse_args()

if not os.path.exists(args.uploads):
    os.makedirs(args.uploads)


class BadgeServer(BaseHTTPRequestHandler):

    def do_GET(self):  # pylint: disable=invalid-name
        if self.path == "/":
            body = _list_contents(args.uploads)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Content-Type", "application/json")
            self.send_response(200, "OK")
            self.wfile.write(body.encode("utf-8"))
        else:
            self.send_response(404)

    def do_DELETE(self):  # pylint: disable=invalid-name
        self.send_response(405, "Method Not Allowed")

    def do_POST(self):  # pylint: disable=invalid-name
        self.send_response(405, "Method Not Allowed")

    def do_PUT(self):  # pylint: disable=invalid-name
        basename = os.path.basename(self.path)
        path = f"{args.uploads}/{basename}"
        print(f"Resolved output path {path}")

        if os.path.exists(path):
            body = f"{basename} already exists"
            self.send_response(409, "Conflict")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(body.encode("utf-8"))
            return

        content_length = int(self.headers["Content-Length"])
        with open(path, "wb") as output:
            output.write(self.rfile.read(content_length))

        body = f"Saved {basename}"
        self.send_response(201, "Created")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))


if __name__ == "__main__":
    webServer = HTTPServer((args.host, int(args.port)), BadgeServer)
    print(f"Server started http://{args.host}:{args.port}")

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")


def _list_contents(path: str):
    return json.dumps(next(walk(args.uploads), (None, None, []))[2])
