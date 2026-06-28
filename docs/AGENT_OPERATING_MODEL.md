# Agent Operating Model

MT5 Robot Lab agents operate through branch-isolated Grand MVP missions.

## Roles

- Director: chooses the next MVP and confirms mission authorization.
- MVP Planner: turns product goals into a scoped MVP.
- Decomposer: splits the MVP into safe modules.
- Builder: implements app, docs, tests or tooling.
- Validator: runs local validation, publication guard and scope checks.
- PR Manager: stages, commits, pushes and opens a draft PR.

## Rules

- Work only inside `E:\mt5-robot-lab`.
- Do not touch `ea-xau`.
- Do not touch PayoffGrid.
- Do not touch ONPN11.
- Do not copy private files.
- Do not run real MT5 unless explicitly authorized.
- Do not create `.exe`, `.zip`, releases or tags unless explicitly authorized.
- Preserve a no-CLI final user experience.
- Keep Codex assisted mode optional.

## Handoff

Each MVP ends with validation output, branch, commit, PR URL, limitations and
next recommended MVP.
