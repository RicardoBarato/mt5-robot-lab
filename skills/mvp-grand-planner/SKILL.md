name: mvp-grand-planner
purpose: Plan large MT5 Robot Lab MVP batches with scope, risks, validation and handoff.
when_to_use: Use before starting a Grand MVP or when converting product goals into executable missions.
inputs: Product objective, allowed scope, forbidden scope, existing roadmap and validation requirements.
outputs: MVP plan with objective, files, tests, risk, rollback plan and final report target.
hard_rules:
- do not touch ea-xau
- do not touch PayoffGrid
- do not touch ONPN11
- do not copy private files
- do not run real MT5 unless mission explicitly allows
- do not create releases/tags unless mission explicitly allows
validation: Confirm scope, files, tests, publication guard and PR target before execution.
handoff: Send the decomposed MVP to mvp-decomposer or the executing agent with explicit boundaries.
