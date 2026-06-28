name: codex-scope-guard
purpose: Enforce repository and artifact boundaries during MT5 Robot Lab work.
when_to_use: Use at mission start, before broad searches, before staging and before PR creation.
inputs: Mission scope, current working directory, changed files and forbidden project list.
outputs: Scope decision, boundary warnings and safe continuation or abort recommendation.
hard_rules:
- do not touch ea-xau
- do not touch PayoffGrid
- do not touch ONPN11
- do not copy private files
- do not run real MT5 unless mission explicitly allows
- do not create releases/tags unless mission explicitly allows
validation: Verify all commands, reads, writes and git operations stay inside E:\mt5-robot-lab.
handoff: If scope is clean, continue to implementation; if not, abort and report SCOPE_VIOLATION_RISK=true.
