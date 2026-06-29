# Post-Merge Validation Fix Report

## Summary

This fix stabilizes validation after MetaTrader 5 was installed on the local machine.

Two post-merge failures were addressed:

- Unit tests for custom MT5 path handling could fall back to real system autodetection.
- The publication guard scanned local-only diagnostics preserved under `reports/private`.

## Test Isolation Fix

`detect_mt5([])` now treats an empty root list as an explicit instruction to scan no system locations.

This keeps unit tests deterministic when they create fake `terminal64.exe` and `metaeditor64.exe` files in temporary directories. Tests that validate absent or invalid custom paths no longer depend on whether MT5 exists on the operator machine.

## Publication Guard Fix

`tools/publication_guard.py` now skips local-only private output folders by default, including:

- `reports/private/`
- `runs/`

The guard also respects Git-ignored files by default outside the public scan scope.

## Public Boundary

`reports/public` remains protected. Public reports are still scanned for forbidden artifact names, sensitive terms, local path leaks and unsafe claims.

Regression tests now confirm:

- local diagnostics under `reports/private` are ignored by default;
- equivalent leaks under `reports/public` are still detected.

## Execution Boundary

- MT5 real run: false
- Strategy Tester run: false
- Backtest real run: false
- EA executed: false
- Tournament 100 run: false
- Credentials stored: false

## Next Step

After this fix is reviewed and merged, rerun local MT5 detection from a clean `main` branch before preparing the gated one-run real MT5 smoke.
