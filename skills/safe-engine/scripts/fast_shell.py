"""Shell command parsing for fast_gate.py hooks: files a command writes, whether it scaffolds, and each simple command
(words, env, input, judged text) for the destructive guard (fast_rules.py, fast_guard.py).

Pure string analysis; callers resolve paths. Heredoc bodies, PowerShell here-strings and quoted text never count as
code for writes and scaffolds, so ticket bodies with "->" or "npm install" pass. Quoted redirect targets count.
"""
from collections import namedtuple
from functools import lru_cache
from itertools import dropwhile
import re

HEREDOC = re.compile(r"(?<!<)<<-?[ \t]*(['\"]?)(\w+)\1")  # the header; the body ends at a line with the tag
HERESTRING = re.compile(r"@'.*?^'@|@\".*?^\"@", re.S | re.M)
QUOTED = re.compile(r"'[^']*'|\"(?:\\.|[^\"\\])*\"", re.S)
ARITHMETIC = re.compile(r"\(\((?:[^()]|\([^()]*\))*\)\)|\[\[[^\]]*\]\]")
TARGET = r"(\x00\d+\x00|[^\s;&|<>()'\"\x00]+)"
REDIRECT = re.compile(r"(?<![<>])[&\d]?>>?\|?[ \t]*" + TARGET + r"|\|[ \t]*tee\b(?:[ \t]+-a)?[ \t]+" + TARGET)
SCAFFOLD = re.compile(
    r"\b(?:(?:npm|pnpm|yarn|bun)\s+(?:create|init|install|i|add)\b|(?:npx|pnpx|bunx|pnpm\s+dlx)\s+(?:-\S+\s+)*"
    r"(?:create-|shadcn|@\S+/create)|cargo\s+(?:new|init|add)\b|dotnet\s+new\b|go\s+mod\s+init\b|"
    r"flutter\s+create\b|rails\s+new\b|django-admin\s+startproject\b|(?:pip|uv|poetry)\s+(?:install|add|init|new)\b)",
    re.I)
DISCARD = ("/dev/null", "nul", "$null")
SUBSTITUTE = ((re.compile(r"\$\{(\w+)\}"), r"$\1"), (re.compile(r"\$\(\s*pwd\s*\)"), "$PWD"),
              (re.compile(r"\$\(\s*git\s+rev-parse\s+--show-toplevel\s*\)"), "$GIT_TOPLEVEL"))
PIPELINES = re.compile(r"([()])|\|\||&&|[;\n{}]|(?<![<>|])&(?!>)")  # ( and ) kept: they open and close a scope
TOKEN = re.compile(r"\d*(?:<<<|<<|<|&?>>?)(?:&[\d-]|\|)?|(?:\\\s|[^\s<>])+")  # a redirect operator, or a word
PLACEHOLDER = re.compile(r"\x00(\d+)\x00")
CAT_HEREDOC = re.compile(r"\$\(\s*cat\s*<<(?:(?!\$\(|`).)*\)\s*", re.S)  # $(cat <<'EOF' ...) with no code inside
ASSIGN = re.compile(r"\w+=")
EXPORT = re.compile(r"(?:export|set|setx)$|\$env:\w+=", re.I)
NUMBER = re.compile(r"[\d.]+[smhd]?")
MAX_DEPTH = 20  # nested shell strings; deeper is unreadable, never an agent's command
KEYWORDS = {"if", "then", "else", "elif", "elseif", "fi", "do", "done", "while", "until", "for", "in", "case", "esac",
            "!", "{", "}", "try", "catch", "finally", "&"}
GROUP_OK = {"if", "elseif", "while", "until", "for", "foreach", "switch", "catch", "!"}  # words a ( may follow
WRAPPERS = {"sudo", "doas", "env", "timeout", "time", "nice", "nohup", "command", "exec", "stdbuf", "ionice",
            "builtin", "start", "npx", "pnpx", "bunx"}
SHELLS = {"bash", "sh", "zsh", "dash", "ksh", "fish", "su"}
STDIN_SHELLS = SHELLS | {"pwsh", "powershell", "cmd"}
CLIENTS = {"psql", "mysql", "mariadb", "sqlite3", "sqlcmd", "mongosh", "mongo", "duckdb", "sqlplus",
           "clickhouse-client", "mysqlsh", "pgcli"}
ECHOES = {"echo", "printf", "write-output"}
SEARCHERS = {"grep", "egrep", "fgrep", "rg", "findstr", "select-string", "sls"}
MESSAGES = {"-m", "--message", "-F", "--body", "--title", "--notes", "--grep"}
PATTERN_FLAGS = {"-e", "--regexp", "-pattern"}
CD = {"cd", "pushd", "popd", "chdir", "set-location", "sl", "push-location", "pop-location"}
UNREADABLE = "\x00unreadable"  # an undecodable or too deep command; NUL never survives mask(), so none can forge it
UNCLEAR = "\x00unclear"  # a $( ), backtick or mid-command group the parse cannot follow
Command = namedtuple("Command", "words env inputs text outer", defaults=("", False))


def bodies(text, hold):
    """text with each heredoc body held after its `<<`. Linear: an unterminated body ends the scan."""
    out, at = [], 0
    while True:
        head = HEREDOC.search(text, at)
        line = text.find("\n", head.end()) if head else -1
        end = line >= 0 and re.compile(rf"^[ \t]*{head.group(2)}[ \t]*$", re.M).search(text, line + 1)
        if not end:
            return "".join(out) + text[at:]
        body = text[line + 1:end.end()]
        if head.group(1):  # a quoted tag: the body never expands, so its $( and backticks are plain text
            body = body.replace("$(", "$ (").replace("`", "'")
        out.append(text[at:head.start()] + "<<" + hold(body) + text[head.end():line])
        at = end.end()


@lru_cache(maxsize=16)
def mask(command):
    """(code, quotes): heredoc bodies, here-strings, quoted strings and arithmetic become numbered placeholders.
    Cached: writes, scaffolds and the guard share one mask per hook event."""
    quotes = []

    def hold(text):
        quotes.append(text)
        return f"\x00{len(quotes) - 1}\x00"

    text = command.replace("\x00", "")
    for pattern, value in SUBSTITUTE:
        text = pattern.sub(value, text)
    text = HERESTRING.sub(lambda match: hold(match.group(0)[2:-2]), bodies(text, hold))
    text = QUOTED.sub(lambda match: hold(match.group(0)[1:-1]), text)
    return ARITHMETIC.sub(lambda match: f" {hold(match.group(0))} ", text), tuple(quotes)


def writes(command):
    """Target paths the command writes through redirects (> >> &> 1> >|) or a piped tee."""
    code, quotes = mask(command)
    names = []
    for first, second in REDIRECT.findall(code):
        name = unquote(first or second, quotes)
        if name and name[0] not in "&$" and name.lower() not in DISCARD:
            names.append(name)
    return names


def unquote(word, quotes):
    """word with placeholders back to their text, nested ones too (a quote inside a held body)."""
    for _ in range(4):
        if "\x00" not in word:
            break
        word = PLACEHOLDER.sub(lambda match: quotes[int(match.group(1))], word)
    return word


def scaffolds(command):
    """True when the command's code (not its quoted text or bodies) scaffolds or installs packages."""
    return bool(SCAFFOLD.search(mask(command)[0]))


def program(word):
    """Bare program name: no folder, no .exe, lower case."""
    return re.sub(r"\.exe$", "", re.split(r"[\\/]", word)[-1].lower())


def literal(word):
    """True when word cannot run code: no $( ) or backtick, or only a quoted-tag heredoc fed to cat."""
    return not re.search(r"\$\(|`", word) or bool(CAT_HEREDOC.fullmatch(word))


def parse(piece, quotes):
    """One simple command, redirects split off; reserved words and wrappers (sudo -u x, timeout 10) skipped."""
    words, env, inputs = [], [], []
    tokens = iter(TOKEN.findall(piece))
    for token in tokens:
        if "<" not in token and ">" not in token:
            words.append(unquote(token.replace("\\ ", " "), quotes))
            continue
        target = "" if re.search(r"&[\d-]$", token) else next(tokens, "")
        if "<" in token:
            inputs.append((token.lstrip("0123456789"), unquote(target, quotes)))
    while words and (ASSIGN.match(words[0]) or program(words[0]) in WRAPPERS | KEYWORDS):
        wrapper = program(words[0]) in WRAPPERS
        env.append(words.pop(0))
        while wrapper and words and (words[0].startswith("-") or NUMBER.fullmatch(words[0])):
            if words.pop(0) in ("-u", "-g", "-n", "-s", "-k") and words:
                words.pop(0)  # the option's value
    return Command(words, env, inputs) if words else None


def said(cmd, feeds):
    """The command's judged text: env, words and input, minus literal message and data text (commit and PR text,
    search patterns, echo arguments and heredocs unless fed to a shell or database client)."""
    words, name = cmd.words, program(cmd.words[0])
    cut = {i for i in range(1, len(words))
           if words[i - 1] in MESSAGES or ("=" in words[i] and words[i].split("=")[0] in MESSAGES)}
    if name in ECHOES and not feeds:
        cut.update(range(1, len(words)))
    if name in SEARCHERS:  # the first free word is the pattern, and so is the value of -e / -Pattern
        cut.update(i for i in range(1, len(words)) if words[i - 1].lower() in PATTERN_FLAGS)
        cut.add(next((i for i in range(1, len(words)) if not words[i].startswith("-")), len(words)))
    kept = [w for i, w in enumerate(words) if i not in cut or not literal(w)]
    code = feeds or name in STDIN_SHELLS | CLIENTS  # else a heredoc is data, such as a file being written
    return " ".join(cmd.env + kept + [text for op, text in cmd.inputs if op == "<" or code or not literal(text)])


def nested(words):
    """The command string a shell -c, su -c, eval, cmd /c or PowerShell runs from its arguments; UNREADABLE when
    an -EncodedCommand cannot be decoded; None when the arguments hold no command string."""
    name, args = program(words[0]), words[1:]
    if name == "eval" or (name == "powershell" and args and not args[0].startswith("-")):
        return " ".join(args)
    if name not in STDIN_SHELLS:
        return None
    for index, arg in enumerate(args):
        flag = arg.lower()
        if name in SHELLS and re.fullmatch(r"-[a-z]*c[a-z]*", flag):
            return args[index + 1] if index + 1 < len(args) else ""
        if (name == "cmd" and flag in ("/c", "/k")) or (
                name in ("pwsh", "powershell") and (flag == "-c" or (len(flag) > 3 and "-command".startswith(flag)))):
            return " ".join(args[index + 1:])
        if name in ("pwsh", "powershell") and (flag in ("-e", "-ec") or (
                len(flag) > 3 and "-encodedcommand".startswith(flag))):
            import base64  # rare: keep it off the hook's hot path
            try:
                return base64.b64decode(args[index + 1], validate=True).decode("utf-16-le")
            except (IndexError, ValueError):
                return UNREADABLE
    return None


def fed(cmd):
    """Literal text a command hands on: echo, printf or Write-Output arguments, else its heredoc or here-string."""
    if program(cmd.words[0]) in ECHOES:
        return " ".join(dropwhile(lambda w: w.startswith("-"), cmd.words[1:]))
    return "\n".join(text for op, text in cmd.inputs if op.startswith("<<")) or None


def runs(pieces, index):
    """The command string pieces[index] runs: its own argument string, or, for a shell, its literal stdin (its
    heredoc or here-string and the literal output of the piece piped into it); None when it runs none."""
    cmd = pieces[index]
    found = nested(cmd.words)
    if found is None and program(cmd.words[0]) in STDIN_SHELLS:
        texts = [fed(cmd)] + ([fed(pieces[index - 1])] if index else [])
        found = "\n".join(text for text in texts if text) or None
    return found


def feeding(pieces, index):
    """True when pieces[index] pipes literal text into a shell that reads it as code."""
    after = pieces[index + 1] if index + 1 < len(pieces) else None
    return bool(after and program(after.words[0]) in STDIN_SHELLS and nested(after.words) is None
                and fed(pieces[index]) is not None)


def pipelines(command, exported=None, depth=0):
    """Commands in order, with "(" and ")" around a subshell or a nested command string. A Command whose code is
    parsed in place (shell -c, eval, literal stdin) is outer. export, set and $env: words join every later env."""
    exported = [] if exported is None else exported
    if depth > MAX_DEPTH:
        yield Command([UNREADABLE], [], [], UNREADABLE)
        return
    code, quotes = mask(command)
    if "`" in code:
        yield Command([UNCLEAR], [], [], UNCLEAR)
    last = ""
    for part in PIPELINES.split(code):
        if part in ("(", ")"):
            if part == "(" and last.split() and last.split()[-1].lower() not in GROUP_OK:
                yield Command([UNCLEAR], [], [], UNCLEAR)
            yield part
            last = ""
            continue
        last = part or ""
        pieces = [cmd for cmd in (parse(piece, quotes) for piece in last.split("|")) if cmd]
        for index, cmd in enumerate(pieces):
            if EXPORT.match(program(cmd.words[0])):
                exported += cmd.words
            inner, cmd = runs(pieces, index), cmd._replace(env=exported + cmd.env)
            after = program(pieces[index + 1].words[0]) if index + 1 < len(pieces) else ""
            text = said(cmd, after in STDIN_SHELLS | CLIENTS)
            yield cmd._replace(text=text, outer=inner is not None or feeding(pieces, index))
            if inner == UNREADABLE:
                yield Command([UNREADABLE], [], [], UNREADABLE)
            elif inner is not None:
                yield "("
                yield from pipelines(inner, exported, depth + 1)
                yield ")"


def cd_target(words):
    """Where cd, pushd, Set-Location or their kin go: a path, '~' with none, '' when unknown; None if not a cd."""
    name = program(words[0])
    if name not in CD:
        return None
    args = [w for w in words[1:] if not (w.startswith("-") and len(w) > 1) and w.lower() != "/d"]
    return "" if name in ("popd", "pop-location") or "-" in args else (args[0] if args else "~")
