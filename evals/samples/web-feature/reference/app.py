"""Notes service: a WSGI app. Run `python app.py` to serve it on http://127.0.0.1:8000."""
import json
from urllib.parse import parse_qs
from wsgiref.simple_server import make_server

NOTES = []


def respond(start_response, status, body):
    """Send `body` as JSON with `status`."""
    data = json.dumps(body).encode("utf-8")
    start_response(status, [("Content-Type", "application/json"), ("Content-Length", str(len(data)))])
    return [data]


def create(environ, start_response):
    """Store a note from a JSON body {"text": "..."}; 400 when the body or text is invalid."""
    try:
        size = int(environ.get("CONTENT_LENGTH") or 0)
        body = json.loads(environ["wsgi.input"].read(size) or b"null")
    except (ValueError, KeyError):
        return respond(start_response, "400 Bad Request", {"error": "body must be JSON"})
    text = body.get("text") if isinstance(body, dict) else None
    if not isinstance(text, str) or not text.strip():
        return respond(start_response, "400 Bad Request", {"error": "text must be a non-empty string"})
    note = {"id": len(NOTES) + 1, "text": text}
    NOTES.append(note)
    return respond(start_response, "201 Created", note)


def listing(environ, start_response):
    """List notes, filtered by ?q= substring, case-insensitively."""
    query = parse_qs(environ.get("QUERY_STRING", "")).get("q", [""])[0].lower()
    return respond(start_response, "200 OK", [note for note in NOTES if query in note["text"].lower()])


def app(environ, start_response):
    """Route requests: GET /notes lists, POST /notes creates."""
    if environ.get("PATH_INFO") == "/notes":
        method = environ.get("REQUEST_METHOD")
        if method == "GET":
            return listing(environ, start_response)
        if method == "POST":
            return create(environ, start_response)
    return respond(start_response, "404 Not Found", {"error": "not found"})


if __name__ == "__main__":
    make_server("127.0.0.1", 8000, app).serve_forever()
