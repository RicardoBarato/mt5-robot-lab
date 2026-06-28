name: mvp-decomposer
purpose: Break a Grand MVP into safe implementation modules that can be validated independently.
when_to_use: Use after planning and before implementation when an MVP spans app, docs, tests and tooling.
inputs: Grand MVP plan, expected files, risk flags and validation commands.
outputs: Ordered module list, dependency notes, rollback plan and completion checklist.
hard_rules:
- do not touch ea-xau
- do not touch PayoffGrid
- do not touch ONPN11
- do not copy private files
- do not run real MT5 unless mission explicitly allows
- do not create releases/tags unless mission explicitly allows
validation: Ensure each module can be tested without real MT5, real backtests or private artifacts.
handoff: Send module sequence to the relevant builder skill or implementation agent.
