"""Rubric for the web-feature sample: requests run against the candidate's WSGI app in a harness process.

Each check runs its requests in one fresh harness process, so the in-memory notes start empty. Fixed cases stay;
fresh random notes and queries are answered by the reference app (REFERENCE, in this process) and must match.
"""
from evals.rubric_tools import RANDOM, agree, answers, call, expect, request, same

WORDS = ("milk", "bread", "call", "mom", "pay", "rent", "walk", "dog", "read", "book", "fix", "bike")


def phrase():
    """A random note text of a few words in random case."""
    return " ".join(RANDOM.choice((str.lower, str.upper, str.title))(RANDOM.choice(WORDS))
                    for _ in range(RANDOM.randint(1, 4)))


def reference():
    return REFERENCE["app.py"]  # noqa: F821 - provided by the check program


def create(work):
    """R1: POST /notes stores a note and answers 201 with id and text; ids start at 1."""
    first, second = call(work, "app", [request("POST", "/notes", {"text": "buy milk"}),
                                       request("POST", "/notes", {"text": "call mom"})])
    expect(first, [201, {"id": 1, "text": "buy milk"}], "first POST")
    expect(second, [201, {"id": 2, "text": "call mom"}], "second POST")
    posts = [request("POST", "/notes", {"text": phrase()}) for _ in range(RANDOM.randint(2, 5))]
    agree(work, "app", reference(), posts, "random POST")


def invalid(work):
    """R2: bad JSON or a bad text answers 400 with an error and stores nothing. Valid POSTs are shuffled in, so
    answering 400 to everything fails; they and the final listing must match the reference."""
    garbage = "".join(RANDOM.choice("{[:,x") for _ in range(RANDOM.randint(1, 6))) + "{"
    bad = ["{not json", garbage, {}, {"text": ""}, {"text": RANDOM.randint(-99, 99)}, {"text": [phrase()]}]
    bodies = [(False, body) for body in bad] + [(True, {"text": phrase()}) for _ in range(RANDOM.randint(2, 4))]
    RANDOM.shuffle(bodies)
    ops = [request("POST", "/notes", body) for _, body in bodies] + [request("GET", "/notes")]
    *wants, listing = answers(reference(), "app", ops)  # expected, from the reference, before the candidate runs
    *gots, got_listing = call(work, "app", ops)
    for (valid, body), want, (status, value) in zip(bodies, wants, gots):
        if valid:
            assert same([status, value], want), f"valid {body!r}: expected {want[1]!r}, got {[status, value]}"
            continue
        ok = status == "ok" and value[0] == 400 and type(value[1]) is dict and type(value[1].get("error")) is str
        assert ok and value[1]["error"], f"{body!r}: got {[status, value]}"
    assert same(got_listing, listing), f"listing after mixed POSTs: expected {listing[1]!r}, got {got_listing}"


def search(work):
    """R3: GET /notes?q= filters by substring, case-insensitively; no q lists all."""
    *posts, found, every = call(work, "app", [request("POST", "/notes", {"text": text})
                                              for text in ("Buy MILK", "call mom", "milkshake")]
                                + [request("GET", "/notes", query="q=milk"), request("GET", "/notes")])
    assert all(status == "ok" and value[0] == 201 for status, value in posts), f"setup POSTs: {posts}"
    texts = [note.get("text") for note in found[1][1]] if found[0] == "ok" and type(found[1][1]) is list else found
    expect(["ok", texts], ["Buy MILK", "milkshake"], "q=milk")
    assert every[0] == "ok" and type(every[1][1]) is list and len(every[1][1]) == 3, f"GET /notes: {every}"
    word = RANDOM.choice(WORDS)
    query = RANDOM.choice((str.lower, str.upper))(word[:RANDOM.randint(2, len(word))])
    ops = [request("POST", "/notes", {"text": phrase()}) for _ in range(RANDOM.randint(3, 6))]
    agree(work, "app", reference(), ops + [request("GET", "/notes", query=f"q={query}"), request("GET", "/notes")],
          "random search")


CHECKS = {"R1": create, "R2": invalid, "R3": search}
