"""Rubric for the web-feature sample: requests run against the candidate's WSGI app in a harness process.

Each check runs its requests in one fresh harness process, so the in-memory notes start empty.
"""
from evals.rubric_tools import call, expect, request


def create(work):
    """R1: POST /notes stores a note and answers 201 with id and text; ids start at 1."""
    first, second = call(work, "app", [request("POST", "/notes", {"text": "buy milk"}),
                                       request("POST", "/notes", {"text": "call mom"})])
    expect(first, [201, {"id": 1, "text": "buy milk"}], "first POST")
    expect(second, [201, {"id": 2, "text": "call mom"}], "second POST")


def invalid(work):
    """R2: bad JSON or a bad text answers 400 with an error and stores nothing."""
    bodies = ("{not json", {}, {"text": ""}, {"text": 5})
    *answers, listing = call(work, "app", [request("POST", "/notes", body) for body in bodies]
                             + [request("GET", "/notes")])
    for body, (status, value) in zip(bodies, answers):
        ok = status == "ok" and value[0] == 400 and type(value[1]) is dict and type(value[1].get("error")) is str
        assert ok and value[1]["error"], f"{body!r}: got {[status, value]}"
    expect(listing, [200, []], "an invalid POST stored a note")


def search(work):
    """R3: GET /notes?q= filters by substring, case-insensitively; no q lists all."""
    *posts, found, every = call(work, "app", [request("POST", "/notes", {"text": text})
                                              for text in ("Buy MILK", "call mom", "milkshake")]
                                + [request("GET", "/notes", query="q=milk"), request("GET", "/notes")])
    assert all(status == "ok" and value[0] == 201 for status, value in posts), f"setup POSTs: {posts}"
    texts = [note.get("text") for note in found[1][1]] if found[0] == "ok" and type(found[1][1]) is list else found
    expect(["ok", texts], ["Buy MILK", "milkshake"], "q=milk")
    assert every[0] == "ok" and type(every[1][1]) is list and len(every[1][1]) == 3, f"GET /notes: {every}"


CHECKS = {"R1": create, "R2": invalid, "R3": search}
