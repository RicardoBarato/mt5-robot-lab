# Public Repository Governance

MT5 Robot Lab is the main desktop software project for local MetaTrader 5
research workflows. It is not a trading signal, managed account, broker product
or live trading system.

## Repository Role

- MT5 Robot Lab is the main desktop software.
- `ea-xau` is an external XAUUSD laboratory and ranking archive.
- Future laboratories can connect through documented interfaces, but they remain
  separate repositories unless explicitly approved.
- PayoffGrid is untouchable from this project.
- ONPN11 / financial-panel-br is untouchable from this project.

## Current Technical Boundary

- MT5 real execution is not integrated yet.
- Real backtests have not been run from this software yet.
- The app must not redistribute MetaTrader 5 in any installer.
- The app must not bundle broker installers, account data, server details,
  passwords, tokens or credentials.
- Codex assisted mode is optional and must require explicit user authorization.
- The end user should not need manual CLI usage for normal product workflows.

## Public Artifact Boundary

The public repository must not contain:

- `.set` presets from real use;
- `.ex5` compiled binaries;
- real MT5 logs;
- raw private reports;
- private account, broker or server details;
- passwords, tokens, API keys or credentials;
- local machine paths from private workspaces.

## Change Governance

- All changes after the initial scaffold must use a branch and pull request.
- `main` must remain protected.
- CI must pass before merge.
- CI must not run real MT5, real Strategy Tester jobs or live trading.
- Public documentation must not promise profit or present research as financial
  advice.
