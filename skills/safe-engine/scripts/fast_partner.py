"""Owner profile and technical-partner config (.agents/skills/safe-engine/references/partner.md).

Both live outside every project: the profile in the gate home, the partner in this bundle with an optional
override in the gate home. A project can never name the recipient, so a planted config cannot redirect a brief.
Values are checked where they enter; anything else is refused loudly. Python 3.9+, stdlib only.
"""
import json
import re
from pathlib import Path
from urllib.parse import quote

PROFILE = {"tech": ("developer", "some", "non-technical", "team"),
           "role": ("founder", "agency", "employee", "hobby"), "offers": ("on", "off")}
SILENT = {"developer", "team"}  # tech levels that never get offers
FIELDS = ("name", "email", "site", "book", "packages")
EMAIL = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")
# The recorded decision. Its twin in safe_engine/workflow.py (PARTNER) must match: the controller cannot import this.
DECISION = re.compile(r"(?:offered|sent|declined|none) \([^()\n]*\S[^()\n]*\)", re.I)
BUNDLED = Path(__file__).resolve().parent.parent / "partner.json"
MAILTO_MAX = 1800  # longer mail links break in common mail apps; the caller prints the text instead


def read_json(path):
    """A JSON object from path; {} when absent. A present but broken file is an error, never an empty default."""
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must hold a JSON object")
    return data


def owner(home):
    """The saved profile, keeping only known keys with allowed values."""
    data = read_json(Path(home) / "owner.json")
    return {key: value for key, value in data.items() if value in PROFILE.get(key, ())}


def set_owner(home, pairs):
    """Save key=value pairs after checking each one; returns the new profile."""
    profile = owner(home)
    for pair in pairs:
        key, _, value = pair.partition("=")
        if value not in PROFILE.get(key, ()):
            allowed = "; ".join(f"{name}: {', '.join(values)}" for name, values in PROFILE.items())
            raise ValueError(f"Unknown owner value '{pair}'. Allowed: {allowed}")
        profile[key] = value
    path = Path(home) / "owner.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(profile, indent=2) + "\n", encoding="utf-8")
    return profile


def forget_owner(home):
    """Delete the profile; the next offer asks again."""
    (Path(home) / "owner.json").unlink(missing_ok=True)


def partner(home, bundled=BUNDLED):
    """The configured partner, or None when none is set. The gate-home override wins over the bundle."""
    override = Path(home) / "partner.json"
    data = read_json(override if override.is_file() else bundled)
    email = str(data.get("email") or "").strip()
    if not email:
        return None
    if not EMAIL.fullmatch(email):
        raise ValueError(f"Partner email '{email}' is not an address; fix partner.json")
    return {key: data.get(key) or ([] if key == "packages" else "") for key in FIELDS} | {"email": email}


def offers_on(profile, config):
    """Whether this owner may get unprompted offers."""
    return bool(config) and profile.get("offers") != "off" and profile.get("tech") not in SILENT


def owner_line(home):
    """One line for `start`: who the owner is and whether offers are on."""
    try:
        profile, config = owner(home), partner(home)
    except (OSError, ValueError) as error:
        return f"👤 owner: unreadable profile or partner config ({error})"
    who = " ".join(filter(None, (profile.get("tech", "unknown"), profile.get("role"))))
    state = ("offers on" + ("" if "tech" in profile else ", asked at the first offer")) if offers_on(profile, config) \
        else "offers off" + ("" if config else " (no partner configured)")
    return f"👤 owner: {who} · partner {state}"


def brief(path):
    """(subject, body) from a brief whose first line is 'Subject: ...'."""
    head, _, body = Path(path).read_text(encoding="utf-8").partition("\n")
    if not head.startswith("Subject: ") or not head[9:].strip() or not body.strip():
        raise ValueError("The brief needs a first line 'Subject: <subject>' and a body")
    return head[9:].strip(), body.strip()


def mailto(config, subject, body):
    """A mail link to the partner with subject and body (CRLF line breaks, RFC 6068), or None when too long."""
    body = quote(body.replace("\r\n", "\n").replace("\n", "\r\n"), safe="")
    link = f"mailto:{quote(config['email'], safe='@')}?subject={quote(subject, safe='')}&body={body}"
    return link if len(link) <= MAILTO_MAX else None
