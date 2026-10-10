Extend the notes service in `app.py`. Keep it a WSGI app named `app`, standard library only, notes in memory.

1. `POST /notes` with a JSON body `{"text": "..."}` stores the note and answers `201` with `{"id": <int>, "text": "..."}`. Ids start at 1 and increase by 1.
2. A body that is not JSON, or a `text` that is missing, empty or not a string, answers `400` with `{"error": "<reason>"}` and stores nothing.
3. `GET /notes?q=word` lists only the notes whose text contains `word`, case-insensitively. Without `q` it lists every note.
