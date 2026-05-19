"""Sobe o portal mock em http://localhost:5500"""

import http.server
import socketserver
from pathlib import Path

PORT = 5500
DIRECTORY = Path(__file__).resolve().parent / "portal-mock"


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIRECTORY), **kwargs)


if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Portal mock: http://localhost:{PORT}/login.html")
        print("Credenciais: demo / demo123")
        httpd.serve_forever()
