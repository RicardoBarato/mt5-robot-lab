name: github-pr-manager
purpose: Manage MT5 Robot Lab branch, push and draft PR workflow without bypassing protection.
when_to_use: Use when a mission requires commit, push, PR creation or PR merge checks.
inputs: Branch name, commit message, PR title, PR body, validation status and remote repository.
outputs: Branch, commit, push status, PR URL and merge readiness notes.
hard_rules:
- do not touch ea-xau
- do not touch PayoffGrid
- do not touch ONPN11
- do not copy private files
- do not run real MT5 unless mission explicitly allows
- do not create releases/tags unless mission explicitly allows
validation: Confirm git status, intended staged files, CI requirements and draft PR state.
handoff: Return PR URL and next action to the Director or next MVP agent.
