# User Flow Desktop

Primary screens:

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

The user should not need manual CLI for normal product use.

## Polished Bootstrap Flow

Desktop Navigation v2 turns the early product steps into real in-app screens:

1. Review MT5 status, selected lab, symbol/timeframe and tournament defaults.
2. Detect MT5 from the main screen.
3. Configure the tournament when the setup screen is implemented.
4. Run a dry-run smoke without touching real MT5.
5. Prepare an optional Codex packet only when the user chooses that workflow.
6. Open the public reports folder.
7. Review the Champion DNA placeholder before real candidate data exists.

## Navigation Controller

The app exposes a headless navigation controller with:

- `current_screen`;
- `available_screens`;
- `go_to_screen(screen_id)`;
- `next_screen()`;
- `previous_screen()`.

The default screen is `welcome`. Self-test validates that all 11 screens exist
without opening a GUI.

## Intelligence Mode UX

The default mode is `local_auto`. `codex_assisted` is optional and requires
explicit user authorization. `seeds_only` remains the simplest mode because it
uses included base robots without generating new code mutations.

## Execution Boundary

The polished bootstrap UI still does not run real MT5, real Strategy Tester
backtests, a 100-run tournament, installer generation or portable zip creation.
