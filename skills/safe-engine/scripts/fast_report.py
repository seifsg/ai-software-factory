"""Plain owner reports with explicit per-ticket measurement provenance."""
import re
from pathlib import Path
from urllib.parse import urlsplit

import fast_design as evidence
import fast_worth

CODES = re.compile(r'\b(?:[A-Z]{2,8}-\d+(?:[A-Z]\d+)*|[AURT]\d+(?:[AURT]\d+)*|W\d+-\S*|lane[ -]+[A-Z0-9]+|[0-9a-f]{7,40})\b|(?<!\w)#\d+|\b(?:codex|feat|feature|fix|hotfix|chore|release)/\S+|\bbranch\s+\S+', re.I)
FIELDS = ('feature', 'changed', 'next', 'waiting', 'time_left')
METRICS = ('elapsed_minutes', 'active_minutes', 'tokens', 'planned_minutes', 'planned_tokens')


def plain(value, exceptions=()):
    value = evidence.text(value, 'Report text')
    evidence.require('\n' not in value and '\r' not in value, 'Report fields must be one line')
    for exception in exceptions:
        value = re.sub(r'(?<!\w)' + re.escape(exception) + r'(?!\w)', '', value)
    evidence.require(not CODES.search(value), "Report body contains a code, lane, branch or hash; move it to References")
    return value


def lint(body, exceptions=()):
    """Check every line of a body, never exempt an entire paragraph."""
    for line in body.splitlines():
        if line.strip():
            plain(line, exceptions)


def url(value):
    value = evidence.text(value, 'Reference URL')
    parsed = urlsplit(value)
    evidence.require(parsed.scheme == 'https' and parsed.hostname and not parsed.username and not parsed.password,
                     'References need HTTPS links without credentials')
    return value


def metric(data, ticket, key, seen, exceptions):
    """An unavailable value is not zero; shared measurements cannot become per-ticket totals."""
    evidence.require(isinstance(data, dict), f'{key}: supply measured, estimated or unavailable data')
    status, value = data.get('status'), data.get('value')
    evidence.require(status in ('measured', 'estimated', 'unavailable'), f'{key}: invalid status')
    source = evidence.text(data.get('source'), f'{key} source')
    if status == 'unavailable':
        evidence.require(value is None, f'{key}: unavailable values must be null')
        reason = evidence.text(data.get('reason'), f'{key} reason')
        plain(reason, exceptions)
        return {**data, 'text': 'Unavailable: ' + reason}
    evidence.require(type(value) in (int, float) and 0 <= value <= 10**12, f'{key}: invalid value')
    evidence.require('tokens' not in key or type(value) is int, f'{key}: token counts must be whole numbers')
    evidence.require(data.get('scope') == ticket, f'{key}: measurement must belong to this ticket, never a shared total')
    if key.startswith('planned_'):
        evidence.require(status == 'estimated', f'{key}: plan must be labelled estimated')
    identity = evidence.text(data.get('measurement'), f'{key} measurement identity')
    prior = seen.setdefault((key, identity), ticket)
    evidence.require(prior == ticket, f'{key}: same measurement cannot be allocated to multiple tickets')
    amount = f'{value:,} tokens' if 'tokens' in key else duration(value)
    return {**data, 'source': source, 'text': f'{amount} ({status})'}


def duration(minutes):
    """Show ordinary time units while retaining the exact numeric measurement in the record."""
    seconds = round(minutes * 60)
    if minutes and not seconds:
        return 'Less than 1 second'
    hours, rest = divmod(seconds, 3600)
    mins, secs = divmod(rest, 60)
    parts = [f'{value} {unit}' + ('s' if value != 1 else '')
             for value, unit in ((hours, 'hour'), (mins, 'minute'), (secs, 'second')) if value]
    return ' '.join(parts) or '0 seconds'


def prepare(data, project, tickets):
    """Validate before publication; leave the last accepted report untouched on any failure."""
    evidence.require(type(data.get('version')) is int and data['version'] == 1, 'Report version must be 1')
    rows = data.get('items')
    evidence.require(isinstance(rows, list) and 0 < len(rows) <= 100, 'Report needs 1..100 items')
    supplied = data.get('literal_exceptions', [])
    evidence.require(isinstance(supplied, list) and len(supplied) <= 20, 'Too many literal exceptions')
    exceptions = []
    for row in supplied:
        evidence.require(isinstance(row, dict), 'Literal exception needs exact text and reason')
        literal = evidence.text(row.get('text'), 'Exact product string')
        evidence.require(len(literal) <= 80 and CODES.fullmatch(literal), 'Exception must be one exact code-like product string')
        plain(row.get('reason'))
        exceptions.append(literal)
    seen, linked, items = {}, set(), []
    for row in rows:
        evidence.require(isinstance(row, dict), 'Each report item must be an object')
        ticket = url(row.get('ticket'))
        evidence.require(ticket in tickets and ticket not in linked, 'Report each recorded ticket at most once')
        linked.add(ticket)
        item = {'ticket': ticket}
        for key in FIELDS:
            value = evidence.text(row.get(key), key)
            plain(value, exceptions)
            item[key] = value
        worth = row.get('worth')
        evidence.require(isinstance(worth, dict), 'Worth needs assessment inputs or an unavailable reason')
        if worth.get('unavailable'):
            reason = evidence.text(worth['unavailable'], 'Worth unavailable reason')
            plain(reason, exceptions)
            item['worth_text'] = 'Unavailable: ' + reason
        else:
            assessment = fast_worth.assess(worth)
            item['worth_text'] = ('Not estimated' if assessment['score'] is None else f"{assessment['score']}/7")
            if assessment['mandatory']:
                item['worth_text'] += ' · required'
        item['worth'] = worth
        metrics = row.get('spend')
        evidence.require(isinstance(metrics, dict), 'Supply spend and planned estimates, or unavailable reasons')
        item['spend'] = {key: metric(metrics.get(key), ticket, key, seen, exceptions) for key in METRICS}
        evidence.require(type(row.get('visual')) is bool, 'State whether this item is visual')
        item['visual'] = row['visual']
        picture = row.get('picture')
        if row['visual'] or picture:
            evidence.require(isinstance(picture, dict), 'Visual report needs a current PNG picture')
            caption = evidence.text(picture.get('caption'), 'Picture caption')
            plain(caption, exceptions)
            import fast_image
            path = evidence.local(project, picture.get('path'))
            width, height = fast_image.check(path)
            item['picture'] = {'path': str(path), 'caption': caption, 'sha256': evidence.file_hash(path), 'width': width, 'height': height}
        items.append(item)
    return {'version': 1, 'items': items, 'literal_exceptions': supplied}


def checked_picture(picture, project=None):
    """Reuse a strictly accepted PNG only while its current bytes retain the accepted identity."""
    source = evidence.local(project, picture['path']) if project else Path(picture['path'])
    evidence.require(evidence.file_hash(source) == picture['sha256'], 'Picture changed; capture and publish a fresh report')
    return source


def markdown(report, project=None, current=None):
    """One report body reused by chat and command output, with technical references at the end."""
    lines, refs = [], []
    for i, item in enumerate(report['items'], 1):
        lines += [f"### {item['feature']}", item['changed']]
        if picture := item.get('picture'):
            try:
                source = checked_picture(picture, project)
                caption = picture['caption'].replace('[', r'\[').replace(']', r'\]')
                lines.append(f"![{caption}](<{str(source).replace(chr(92), '/')}>)")
            except (OSError, ValueError):
                lines.append('Picture changed or unavailable; capture and publish a fresh report.')
        if not current:
            lines.append(f"Next: {item['next']}")
        lines.append(f"Worth it: {item['worth_text']}. Time left: {item['time_left']}." +
                     ('' if current else f" Waiting on: {item['waiting']}."))
        spend = item['spend']
        lines += [f"Time spent: {spend['elapsed_minutes']['text']}; active work: {spend['active_minutes']['text']}. Planned: {spend['planned_minutes']['text']}.",
                  f"Tokens used: {spend['tokens']['text']}. Planned: {spend['planned_tokens']['text']}.", '']
        refs.append(f"- [Ticket {i}]({item['ticket']})")
    return '\n'.join(lines + ['References', *refs])
