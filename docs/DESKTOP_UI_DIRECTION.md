# Desktop UI Direction

Official visual direction:

- dark premium;
- black and dark gray surfaces;
- discreet gold primary accent;
- green/red only for status and risk signals;
- clean Windows desktop interface;
- card-based first screen;
- clear primary action for MT5 detection;
- secondary actions for tournament setup, dry-run smoke, Codex packet and reports;
- intelligence mode selector with local automatic as the default;
- Champion DNA placeholder on the first screen;
- no terminal-like first impression.

## First Screen Layout

The opening screen and the navigation shell should immediately communicate that
this is professional desktop software, not a command-line project. The first
viewport includes:

- product title and subtitle;
- bootstrap/dry-run status badge;
- status cards for MT5, lab, symbol/timeframe, balance, max backtests, champion
  count and intelligence mode;
- action bar with the core workflow buttons;
- intelligence mode panel;
- Champion DNA panel.

## Current Visual Contract

The initial implementation uses standard `tkinter` only. No external GUI
dependency is required. Future versions may add optional skinning, but the
fallback must remain usable without additional packages.

## Desktop Navigation v2

MVP-001 adds a sidebar navigation model with 11 product screens:

1. Welcome
2. Lab Selection
3. MT5 Setup
4. Symbol and Timeframe
5. Intelligence Mode
6. Tournament Setup
7. Running Backtests
8. Champions Ranking
9. Champion DNA
10. Export Spreadsheet
11. Settings

The active screen is highlighted. Screen content uses dark cards, clear primary
actions and placeholders for future real MT5 workflows.
