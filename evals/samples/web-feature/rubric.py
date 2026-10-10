"""Rubric for the web-feature sample: calls the candidate WSGI app in process, no network."""
import io
import json
from wsgiref.util import setup_testing_defaults


def call(method, path, body=None, query=""):
    """One request to the candidate's app.app; returns (status code, decoded JSON). Fresh process per check."""
    import app  # the check process puts the workspace first on sys.path
    data = body if isinstance(body, bytes) else json.dumps(body).encode() if body is not None else b""
    environ = {"REQUEST_METHOD": method, "PATH_INFO": path, "QUERY_STRING": query,
               "CONTENT_TYPE": "application/json", "CONTENT_LENGTH": str(len(data)), "wsgi.input": io.BytesIO(data)}
    setup_testing_defaults(environ)
    seen = []
    chunks = app.app(environ, lambda status, headers, exc_info=None: seen.append(status))
    payload = b"".join(chunks)
    assert seen, "app never called start_response"
    return int(seen[0].split()[0]), json.loads(payload or b"null")


def create(work):
    """R1: POST /notes stores a note and answers 201 with id and text; ids start at 1."""
    first, second = call("POST", "/notes", {"text": "buy milk"}), call("POST", "/notes", {"text": "call mom"})
    assert first == (201, {"id": 1, "text": "buy milk"}), f"first POST {first}"
    assert second == (201, {"id": 2, "text": "call mom"}), f"second POST {second}"


def invalid(work):
    """R2: bad JSON or a bad text answers 400 with an error and stores nothing."""
    for body in (b"{not json", {}, {"text": ""}, {"text": 5}):
        status, payload = call("POST", "/notes", body)
        assert status == 400 and isinstance(payload, dict) and payload.get("error"), f"{body!r}: {status} {payload}"
    assert call("GET", "/notes") == (200, []), "an invalid POST stored a note"


def search(work):
    """R3: GET /notes?q= filters by substring, case-insensitively; no q lists all."""
    for text in ("Buy MILK", "call mom", "milkshake"):
        assert call("POST", "/notes", {"text": text})[0] == 201, "setup: POST /notes failed"
    found = call("GET", "/notes", query="q=milk")
    assert found[0] == 200 and [n.get("text") for n in found[1]] == ["Buy MILK", "milkshake"], f"q=milk {found}"
    assert len(call("GET", "/notes")[1]) == 3, "GET /notes without q must list every note"


CHECKS = {"R1": create, "R2": invalid, "R3": search}
