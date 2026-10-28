"""Report publication and standalone body/picture validation through the normal gate."""
from pathlib import Path
from datetime import datetime, timezone
import re

import fast_design as evidence
import fast_report as report


def parser(sub, common):
    command = sub.add_parser('report', parents=[common], help='Publish a plain report or check a body or picture')
    actions = command.add_mutually_exclusive_group(required=True)
    for name in ('file', 'lint', 'picture', 'pr-body'):
        actions.add_argument('--' + name, help='Project-local ' + name)


def run(args, gate):
    """Validate all inputs before replacing the accepted report; identifiers stay in References."""
    try:
        project = gate.find_project(args.project, recover=not args.pr_body)
        if args.picture:
            import fast_image
            width, height = fast_image.check(evidence.local(project, args.picture), project=project)
            print(f'Picture content check passed: {width} × {height}. Inspect the actual result before sharing.')
            return
        if args.lint:
            path = evidence.local(project, args.lint)
            evidence.require(path.stat().st_size <= 100000, 'Report body exceeds 100000 bytes')
            report.lint(path.read_text(encoding='utf-8'))
            print('Report body contains no recognized internal codes.')
            return
        if args.pr_body:
            import fast_pr_policy
            import fast_record
            state = gate.store.current(gate.load(gate.state_path(project)))  # Read without legacy migration.
            evidence.require(gate.well_formed(state), 'Check PR bodies on a readable open run')
            path = evidence.local(project, args.pr_body)
            evidence.require(path.stat().st_size <= 100000, 'PR body exceeds 100000 bytes')
            checked = fast_pr_policy.effective(gate.HOME, state)
            problems = fast_record.pr_body_problems(checked, path.read_text(encoding='utf-8'), project)
            evidence.require(not problems, '\n- '.join(['PR body structure failed:'] + problems))
            print('STRUCTURE ONLY: PR body passed. Handoff, current proofs and review remain required.')
            return
        project, state = gate.open_run(project)
        evidence.require(not state.get('closed'), 'Publish reports on an open run')
        import fast_progress
        sections = fast_progress.read(gate.record_path(project))
        tickets = set(re.findall(r'https://[^\s<>()]+', sections.get('tickets', '')))
        prepared = report.prepare(evidence.read(evidence.local(project, args.file)), project, tickets)
        state['owner_report'] = {**prepared, 'at': datetime.now(timezone.utc).isoformat()}
        gate.put(project, state)
        gate.log('run.report', key=state['key'], items=len(prepared['items']))
        print(report.markdown(state['owner_report']))
    except (OSError, ValueError, KeyError, TypeError) as error:
        gate.fail('Report: ' + str(error))
