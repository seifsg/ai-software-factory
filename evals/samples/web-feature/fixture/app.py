"""Notes service: a WSGI app. Run `python app.py` to serve it on http://127.0.0.1:8000."""
import json
from wsgiref.simple_server import make_server

NOTES = []


def respond(start_response, status, body):
    """Send `body` as JSON with `status`."""
    data = json.dumps(body).encode("utf-8")
    start_response(status, [("Content-Type", "application/json"), ("Content-Length", str(len(data)))])
    return [data]


def app(environ, start_response):
    """Route requests: GET /notes lists every note."""
    if environ.get("PATH_INFO") == "/notes" and environ.get("REQUEST_METHOD") == "GET":
        return respond(start_response, "200 OK", NOTES)
    return respond(start_response, "404 Not Found", {"error": "not found"})


if __name__ == "__main__":
    make_server("127.0.0.1", 8000, app).serve_forever()
