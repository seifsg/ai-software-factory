"""Shell command analysis for fast_gate.py hooks: files a command writes, and whether it scaffolds.

Pure string analysis; callers resolve paths. Heredoc bodies, PowerShell here-strings, quoted text and
shell arithmetic never count as code, so ticket bodies with "->" or "npm install" pass. Quoted redirect
targets still count.
"""
import re

HEREDOC = re.compile(r"(<<-?[ \t]*(['\"]?)(\w+)\2)([^\n]*)\n.*?^[ \t]*\3[ \t]*$", re.S | re.M)
HERESTRING = re.compile(r"@'.*?^'@|@\".*?^\"@", re.S | re.M)
QUOTED = re.compile(r"'[^']*'|\"(?:\\.|[^\"\\])*\"", re.S)
ARITHMETIC = re.compile(r"\(\(.*?\)\)|\[\[.*?\]\]", re.S)
TARGET = r"(\x00\d+\x00|[^\s;&|<>()'\"\x00]+)"
REDIRECT = re.compile(r"(?<![<>])[&\d]?>>?\|?[ \t]*" + TARGET + r"|\|[ \t]*tee\b(?:[ \t]+-a)?[ \t]+" + TARGET)
SCAFFOLD = re.compile(
    r"\b(?:(?:npm|pnpm|yarn|bun)\s+(?:create|init|install|i|add)\b|(?:npx|pnpx|bunx|pnpm\s+dlx)\s+(?:-\S+\s+)*"
    r"(?:create-|shadcn|@\S+/create)|cargo\s+(?:new|init|add)\b|dotnet\s+new\b|go\s+mod\s+init\b|"
    r"flutter\s+create\b|rails\s+new\b|django-admin\s+startproject\b|(?:pip|uv|poetry)\s+(?:install|add|init|new)\b)",
    re.I)
DISCARD = ("/dev/null", "nul", "$null")


def mask(command):
    """(code, quotes): bodies and arithmetic removed, each quoted string replaced by a numbered placeholder."""
    quotes = []

    def keep(match):
        quotes.append(match.group(0)[1:-1])
        return f"\x00{len(quotes) - 1}\x00"

    text = HERESTRING.sub(" ", HEREDOC.sub(r"\1\4", command))
    return ARITHMETIC.sub(" ", QUOTED.sub(keep, text)), quotes


def writes(command):
    """Target paths the command writes through redirects (> >> &> 1> >|) or a piped tee."""
    code, quotes = mask(command)
    names = []
    for first, second in REDIRECT.findall(code):
        name = first or second
        placeholder = re.fullmatch(r"\x00(\d+)\x00", name)
        name = quotes[int(placeholder.group(1))] if placeholder else name
        if name and name[0] not in "&$" and name.lower() not in DISCARD:
            names.append(name)
    return names


def scaffolds(command):
    """True when the command's code (not its quoted text or bodies) scaffolds or installs packages."""
    return bool(SCAFFOLD.search(mask(command)[0]))
