"""Minimal static file server for local preview, avoiding http.server's CLI
module (whose argparse default eagerly calls os.getcwd(), which some sandboxed
environments disallow before the directory is set)."""
import functools
import http.server
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = int(os.environ.get("PORT", 8000))

Handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT)
httpd = http.server.HTTPServer(("", PORT), Handler)
print(f"Serving {ROOT} on port {PORT}")
httpd.serve_forever()
