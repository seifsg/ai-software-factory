# GitHub project boards

Load when the tracker has a project board (`projectItems` not empty).

- Project board with Status field (`projectItems`): set status there, priority too if board has that field.
- Boards: keep built-in workflows that set Done when item closes or its PR merges. Board without Blocked status: add `status: blocked` label too. New issues on a board: `item-add` first.

```text
gh project list --owner <owner>
gh project item-add <project-number> --owner <owner> --url <issue-url>
gh project item-edit <project-number> --owner <owner> --url <issue-url> --field Status --value "In progress"
```
