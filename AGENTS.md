# MT5 Robot Lab Agent Governance

Project identity:

- Product name: `MT5 Robot Lab`.
- Function: Windows desktop software for managing local MetaTrader 5 robot laboratories.
- Official local folder: `E:\mt5-robot-lab`.
- Future official repository: `RicardoBarato/mt5-robot-lab`.

## Scope Boundaries

- Do not touch PayoffGrid / RB Risk Engine AI.
- Do not touch ONPN11 / Quadro Financeiro / financial-panel-br.
- Do not copy private files, memories, raw reports, real presets, `.set`, `.ex5`,
  credentials, account details, broker server details or local private logs.
- `ea-xau` is an external connected laboratory, not the main software product.
- `ea-xau` must not be edited by `mt5-robot-lab` automation.

## Product Rules

- MetaTrader 5 must not be redistributed inside the app.
- Codex Assisted Mode is optional.
- CLI must not be required for the final end-user experience.
- Passwords, tokens and credentials must not be stored.
- Backtests are not a promise of profit.
- Live trading is not authorized by this bootstrap.

## Engineering Rules

- Prefer standard-library Python until a dependency is clearly justified.
- Keep generated private artifacts under ignored folders.
- Keep public reports sanitized.
- Do not create releases, tags, installers or portable zips until a separate
  release mission authorizes them.
- Do not run real MT5 or real backtests during scaffold work.
