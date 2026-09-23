"""Jev-compatible HTTP server: POST /v1/systemone. stdlib only."""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

from .decide import system_one
from .router import route


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/health", "/"):
            return self._send({"ok": True, "model": "tiny-decide-0.1.0"})
        return self._send({"error": "not found"}, 404)

    def do_POST(self):
        if self.path not in ("/v1/systemone", "/systemone"):
            return self._send({"error": "use POST /v1/systemone"}, 404)
        try:
            n = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(n) or b"{}")
        except Exception as e:
            return self._send({"error": "bad json: %s" % e}, 400)
        state = payload.get("state", payload.get("text", ""))
        questions = payload.get("questions", {})
        # normalize Jev shape: questionsFor / list -> dict
        if isinstance(questions, list):
            questions = {q.get("id", str(i)): q for i, q in enumerate(questions)}
        result = system_one(state, questions)
        result["routing"] = route(state, payload.get("lang"))
        return self._send(result)


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8787)
    ap.add_argument("--host", default="127.0.0.1")
    args = ap.parse_args()
    print("tiny-decide serving Jev-compatible API on http://%s:%d/v1/systemone" % (args.host, args.port))
    HTTPServer((args.host, args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
