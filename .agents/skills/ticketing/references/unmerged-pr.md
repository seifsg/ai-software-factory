# PR closed unmerged

At intake, for each closed unmerged PR: each open ticket it names with a closing keyword, unless its activity already records that PR's closing, gets an activity entry (what the PR did, why it closed).

- Another open or merged PR names it: note that superseding PR.
- Otherwise, only while it still sits where that PR left it (Dev done or Ready for QA with that PR linked, no status change since the close), it moves back to Backlog, or closes as not planned when the owner's closing note says it is no longer needed.
- A ticket that moved on keeps its status.
- A redo request in that note is a change of intent for the run that takes it.
