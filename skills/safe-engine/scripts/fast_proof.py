"""PR proof check for the Fast handoff: the PR body's Before & after section, one outcome per heading.

Spec: .agents/skills/how-to-make-a-pr/references/pr-layout.md (Before & after). Text in, problems out; fast_record.py
reads the body (gh or a file). Proves proof was attached and can be opened, not that it is good.
"""
import re

HEADING = re.compile(r"^[ \t]{0,3}(#{1,6})[ \t]+(.+?)[ \t#]*$", re.M)
FENCE = re.compile(r"^[ \t]{0,3}(`{3,}|~{3,})[^\n]*\n(.*?)(?:^[ \t]{0,3}\1[ \t]*$|\Z)", re.M | re.S)
SECTION = re.compile(r"\bbefore\b.*\bafter\b", re.I)
BEFORE = re.compile(r"\*\*Before(?::\*\*|\*\*:)", re.I)
AFTER = re.compile(r"\*\*After(?::\*\*|\*\*:)", re.I)
BOTH = re.compile(r"\*\*Before[ \t]*(?:→|->|/|&|and|vs\.?)[ \t]*After(?::\*\*|\*\*:)"  # '**Before → After:**'
                  r"|^[ \t]*\|[ \t*]*Before[ \t*]*\|[ \t*]*After[ \t*]*\|", re.I | re.M)  # '| Before | After |'
NEW = re.compile(r"\bdid(?: not|n['’]t) exist\b", re.I)
MEDIA = re.compile(r"!\[[^\]\n]*\]\([ \t]*<?([^)\s>]+)"  # ![alt](url)
                   r"|<(?:img|video|source)\b[^>]*?\bsrc[ \t]*=[ \t]*[\"']?([^\"'\s>]+)"  # <img src=url>
                   r"|\[[^\]\n]*\]\([ \t]*<?([^)\s>]+\.(?:png|jpe?g|gif|webp|svg|mp4|webm|mov)(?:\?[^)\s>]*)?)[ \t]*>?\)"
                   r"|(?<![(\"'=<\w/])(https://github\.com/user-attachments/assets/[\w-]+)", re.I)  # bare upload
VIDEO = re.compile(r"\.(?:mp4|webm|mov)(?:\?|$)", re.I)
LOCAL = re.compile(r"https://(?:localhost|127\.|0\.0\.0\.0|\[::1\]|[^/]*\.(?:localhost|local|test)(?:[:/]|$))", re.I)
FILE = re.compile(r"\S*(?:[/\\]\S*|\.[A-Za-z]\w{0,5})")  # one token: a path or a file name
CREDIT = "🏭 Built with [AI Software Factory](https://softwarefactory.company/) by Seif"  # = how-to-make-a-pr credit.md


def problems(body, ui=False):
    """Why the body's Before & after does not report each outcome with openable proof; [] when it does."""
    body = body.replace("\r\n", "\n")  # bodies edited on the web carry CRLF; fences close on bare newlines
    masked = FENCE.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), body)  # same length: code never counts
    heads = [(len(m.group(1)), m.group(2), m.start(), m.end()) for m in HEADING.finditer(masked)]
    start = next((i for i, head in enumerate(heads) if SECTION.search(head[1])), None)
    if start is None:
        return ["needs a '## 🎬 Before & after' section: one heading per outcome (feature, fix, page, module), "
                "each with Before and After proof (how-to-make-a-pr)"]
    rest = heads[start + 1:]
    cut = next((i for i, head in enumerate(rest) if head[0] <= heads[start][0]), len(rest))
    inner, end = rest[:cut], rest[cut][2] if cut < len(rest) else len(body)
    top = min((head[0] for head in inner), default=0)
    outcomes = [head for head in inner if head[0] == top]  # the outcomes; deeper headings belong to them
    if not outcomes:
        return ["Before & after needs one heading per outcome under it: the feature, fix, page or module it changes"]
    found = []
    for (_, title, _, begin), stop in zip(outcomes, [head[2] for head in outcomes[1:]] + [end]):
        found += outcome(title, body[begin:stop], masked[begin:stop])
    links = [m.group(m.lastindex) for m in MEDIA.finditer(masked, heads[start][3], end)]
    found += [f"'{url[:60]}' cannot be opened by a reviewer: upload it and link https" for url in dict.fromkeys(links)
              if not url.lower().startswith("https://") or LOCAL.match(url)]
    if ui and all(VIDEO.search(url) for url in links):
        found.append("this run changed UI: Before & after needs >=1 screenshot")
    return found


def credit(body):
    """The factory credit line closes the PR body (how-to-make-a-pr references/credit.md); [] when it does."""
    lines = [line.strip() for line in body.splitlines() if line.strip()]
    return [] if lines[-1:] == [CREDIT] else [f"end it with the factory credit line, as its last line: {CREDIT}"]


def outcome(title, text, masked):
    """One outcome: named by its effect, Before then After, each with proof; or one combined Before → After."""
    found = ([f"'{title}' names a file: name the feature, fix, page or module it changes"]
             if FILE.fullmatch(re.sub(r"[^\w\s/\\.:-]", "", title).strip()) else [])
    both = BOTH.search(masked)
    if both:
        media, code = MEDIA.findall(masked, both.start()), fences(text, both.start(), len(text))
        if not (any(map(diff, code)) or len(media) >= 2 or (NEW.search(masked) and (media or code))):
            found.append(f"'{title}': Before → After needs a diff block (- or + lines beside others), or two images")
        return found
    before, after = BEFORE.search(masked), AFTER.search(masked)
    if not (before and after and before.start() < after.start()):
        return found + [f"'{title}' needs '**Before:**' then '**After:**', each followed by its proof"]
    if not proof(text, masked, before.end(), after.start()) and not NEW.search(masked, before.end(), after.start()):
        found.append(f"'{title}': Before needs proof: an image, a recording or a fenced block (or 'did not exist')")
    if not proof(text, masked, after.end(), len(text)):
        found.append(f"'{title}': After needs proof: an image, a recording or a fenced block")
    return found


def diff(block):
    """Both sides in one block: changed lines (- or +) beside other changed or unchanged (indented) lines."""
    marks = {line[0] for line in block.splitlines() if line.strip()} & {"-", "+", " "}
    return len(marks) >= 2 and bool(marks - {" "})


def fences(text, start, stop):
    """Contents of the non-empty fenced blocks that open between start and stop."""
    return [m.group(2) for m in FENCE.finditer(text) if start <= m.start() < stop and m.group(2).strip()]


def proof(text, masked, start, stop):
    """An image, a recording or a non-empty fenced block between start and stop."""
    return bool(MEDIA.search(masked, start, stop) or fences(text, start, stop))
