name: validator-release-guard
purpose: Validate public safety before commit, push, PR, release planning or packaging work.
when_to_use: Use before final validation, before PR creation and before any release-adjacent activity.
inputs: Changed files, validation commands, publication guard output and artifact inventory.
outputs: Validation summary, release boundary decision and remaining blockers.
hard_rules:
- do not touch ea-xau
- do not touch PayoffGrid
- do not touch ONPN11
- do not copy private files
- do not run real MT5 unless mission explicitly allows
- do not create releases/tags unless mission explicitly allows
validation: Run compile, tests, self-test, publication guard and git diff checks as applicable.
handoff: Approve PR creation only when checks pass and no forbidden artifacts exist.
