"""PR proof check for the Fast handoff: the PR body's Before & after section, one outcome per heading.

Spec: .agents/skills/how-to-make-a-pr/references/pr-layout.md (Before & after). Text in, problems out; fast_record.py
reads the body (gh or a file). Checks declared proof structure, not media contents or reviewer access.
"""
import re
from urllib.parse import urlsplit

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
COMMENT = re.compile(r"<!--[\s\S]*?(?:-->|\Z)")
INLINE = re.compile(r"(`+)[^\n]*?\1")
LINK = re.compile(r"(!?)\[[^\]\n]*\]\(\s*<?([^\s)>]+)>?(?:[ \t]+[\"'][^\n]*?[\"'])?\)")
SOURCE = re.compile(r"\ssrc\s*=\s*(?:\"([^\"]+)\"|'([^']+)'|([^\s>]+))", re.I)
IMAGE = re.compile(r"\.(?:png|jpe?g|gif|webp|svg)$", re.I)
TABLE = re.compile(r"^[ \t]*\|[ \t*]*Before[ \t*]*\|[ \t*]*After[ \t*]*\|[^\n]*\n"
                   r"[ \t]*\|[ :\-]+\|[ :\-]+\|[^\n]*\n((?:[ \t]*\|[^\n]+\n?)+)", re.I | re.M)


def problems(body, ui=False, demo=False):
    """Why the body's Before & after does not report each outcome with openable proof; [] when it does."""
    body = body.replace("\r\n", "\n")  # bodies edited on the web carry CRLF; fences close on bare newlines
    if demo:
        body = COMMENT.sub(blank, body)
    masked = FENCE.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), body)  # same length: code never counts
    if demo:
        masked = INLINE.sub(blank, masked)
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
    found, visual, videos = [], False, {}
    for (_, title, _, begin), stop in zip(outcomes, [head[2] for head in outcomes[1:]] + [end]):
        if demo:
            issues, is_visual = demonstration(title, body[begin:stop], masked[begin:stop])
            found += issues
            visual |= is_visual
            for line in field(masked[begin:stop], "Video"):
                for kind, url in media(line):
                    if kind == "video":
                        videos.setdefault(url.split("#", 1)[0], []).append((title, line))
        else:
            found += outcome(title, body[begin:stop], masked[begin:stop])
    if demo:
        return found + shared_video_problems(videos) + (["this run changed UI: declare >=1 Visual: yes outcome"] if ui and not visual else [])
    links = [m.group(m.lastindex) for m in MEDIA.finditer(masked, heads[start][3], end)]
    found += [f"'{url[:60]}' cannot be opened by a reviewer: upload it and link https" for url in dict.fromkeys(links)
              if not url.lower().startswith("https://") or LOCAL.match(url)]
    if ui and all(VIDEO.search(url) for url in links):
        found.append("this run changed UI: Before & after needs >=1 screenshot")
    return found


def blank(match):
    """Hide examples and comments without shifting the offsets used for evidence slices."""
    return re.sub(r"[^\n]", " ", match.group(0))


def field(text, label):
    """Read whole-line declarations; duplicates cannot override an earlier obligation."""
    return re.findall(r"^[ \t]*(?:[-*] )?\*\*" + re.escape(label) + r":\*\*[ \t]*(.*)$", text, re.M | re.I)


def public_url(url):
    """Require a plausible external HTTPS address; actual access is checked by the reviewer."""
    try:
        parts = urlsplit(url)
        return bool(parts.scheme == "https" and parts.hostname and parts.port != 0 and not parts.username
                    and not parts.password and not LOCAL.match(url) and not re.search(r"[\s<>\\]", url)
                    and re.fullmatch(r"[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?\.[a-z0-9-]+", parts.hostname))
    except ValueError:
        return False


def media(text):
    """Classify explicit embeds and typed links; an extensionless upload needs an image/video tag."""
    found = []
    for match in LINK.finditer(text):
        image, url = match.groups()
        path = url.split("?", 1)[0].split("#", 1)[0]
        kind = "video" if VIDEO.search(path) else "image" if IMAGE.search(path) or image else None
        if kind and not (image and kind == "video"):
            found.append((kind, url))
    for match in re.finditer(r"<video\b[^>]*>[\s\S]*?</video\s*>|<(?:img|video)\b[^>]*>", text, re.I):
        kind = "image" if match.group(0).lower().startswith("<img") else "video"
        for source in SOURCE.finditer(match.group(0)):
            url = next(value for value in source.groups() if value is not None)
            path = url.split("?", 1)[0].split("#", 1)[0]
            if not (kind == "image" and VIDEO.search(path) or kind == "video" and IMAGE.search(path)):
                found.append((kind, url))
    return found


def declaration(text, label, found):
    """Require an explicit yes or a reasoned no on every outcome."""
    values = field(text, label)
    if len(values) != 1 or not re.fullmatch(r"yes|no[ \t]+\([^\n()]*\S[^\n()]*\)", values[0], re.I):
        found.append(f"needs one '**{label}:** yes' or '**{label}:** no (<reason>)' line")
    return len(values) == 1 and values[0].lower() == "yes"


def shared_video_problems(videos):
    """A shared recording identifies the demonstrated segment for each outcome."""
    timestamp = r"\d{1,2}:\d{2}(?::\d{2})?"
    return [f"'{title}': shared Video needs start/end timestamps on its line" for uses in videos.values()
            if len(uses) > 1 for title, line in uses
            if not re.search(timestamp + r"\s*(?:-|–|→|to)\s*" + timestamp, line)]


def waiver(text, found):
    """Only an outcome's explicit scoped owner request can waive its selected media."""
    values = field(text, "Media waiver")
    if not values:
        return set()
    parts = values[0].split("|", 2)
    if len(values) != 1 or len(parts) != 3 or parts[0].strip().lower() not in {"screenshots", "video", "all"} or not all(
            part.strip() and not re.fullmatch(r"<[^>]+>", part.strip()) for part in parts[1:]):
        found.append("Media waiver needs '<screenshots, video or all> | <owner exact request> | <source>'")
        return set()
    scope = parts[0].strip().lower()
    return {"screenshots", "video"} if scope == "all" else {scope}


def screenshot_sides(text):
    """Separate Before/After labels or table columns keep proof attached to its actual side."""
    before, after = BEFORE.search(text), AFTER.search(text)
    if before and after and before.start() < after.start():
        remaining = re.split(r"(?m)^[ \t]*\*\*(?:Visual|Journey|Video|Media waiver):\*\*", text[after.end():], maxsplit=1)[0]
        return text[before.end():after.start()], remaining
    table = TABLE.search(text)
    if table:
        rows = [line.strip().strip("|").split("|") for line in table.group(1).splitlines()]
        return tuple("\n".join(row[index] for row in rows if len(row) >= 2) for index in (0, 1))
    return None


def demonstration(title, text, masked):
    """Enforce the declared view/journey proof; scope completeness remains an independent review."""
    found = []
    visual = declaration(masked, "Visual", found)
    journey = declaration(masked, "Journey", found)
    waived = waiver(masked, found)
    links = media(masked)
    found += [f"'{url[:60]}' needs an external HTTPS media URL" for _, url in dict.fromkeys(links) if not public_url(url)]
    if visual:
        found += title_problems(title)
        sides = screenshot_sides(masked)
        if not sides:
            found.append("needs '**Before:**' then '**After:**', or a Before | After image table")
        elif "screenshots" in waived and not all(side.strip() for side in sides):
            found.append("waived screenshots still need both Before and After descriptions")
        elif "screenshots" not in waived:
            images = [{url.split("#", 1)[0] for kind, url in media(side) if kind == "image" and public_url(url)} for side in sides]
            if not all(images) or len(images[0] | images[1]) < 2:
                found.append("Visual: yes needs distinct Before and After screenshots (new UI: capture the prior entry state)")
    else:
        found += outcome(title, text, masked)
    if journey and "video" not in waived:
        videos = field(masked, "Video")
        if not any(kind == "video" and public_url(url) for line in videos for kind, url in media(line)):
            found.append("Journey: yes needs a '**Video:**' video link (.mp4/.webm/.mov or explicit HTML video)")
    return [f"'{title}': {problem}" for problem in found], visual


def credit(body):
    """The factory credit line closes the PR body (how-to-make-a-pr references/credit.md); [] when it does."""
    lines = [line.strip() for line in body.splitlines() if line.strip()]
    return [] if lines[-1:] == [CREDIT] else [f"end it with the factory credit line, as its last line: {CREDIT}"]


def outcome(title, text, masked):
    """One outcome: named by its effect, Before then After, each with proof; or one combined Before → After."""
    found = title_problems(title)
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


def title_problems(title):
    """Outcome headings describe an effect, rather than listing implementation files."""
    return ([f"'{title}' names a file: name the feature, fix, page or module it changes"]
            if FILE.fullmatch(re.sub(r"[^\w\s/\\.:-]", "", title).strip()) else [])


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
