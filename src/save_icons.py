"""Serve icons.html locally and save the PNG icons it draws into docs/.

Run `python save_icons.py`, open http://127.0.0.1:8770/icons.html, then call saveAll() in the page.
"""
import http.server, os, sys

SRC = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(os.path.dirname(SRC), "docs")
ALLOWED = {"icon-192.png", "icon-512.png", "icon-maskable-512.png", "apple-touch-icon.png"}


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=SRC, **kwargs)

    def do_POST(self):
        name = self.path.rsplit("/", 1)[-1]
        data = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        if not self.path.startswith("/save/") or name not in ALLOWED or not data.startswith(b"\x89PNG"):
            self.send_error(400)
            return
        os.makedirs(DOCS, exist_ok=True)
        with open(os.path.join(DOCS, name), "wb") as f:
            f.write(data)
        self.send_response(204)
        self.end_headers()


port = int(sys.argv[1]) if len(sys.argv) > 1 else 8770
http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
