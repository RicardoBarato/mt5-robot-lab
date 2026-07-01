# Product UX Gate V2 and Template Intake

Status: HOLD_TEMPLATE_FILES_NOT_FOUND_LOCALLY

## What Changed

- Added Operator Gate V2 for one local smoke approval by CLI flag.
- Added `--run-real-mt5-smoke-once`.
- Added `--approve-one-run-local-smoke`.
- Kept the old long phrase as a deprecated legacy path.
- No real MT5 run was executed.

## Gate V2

- Approval method: cli_flag_one_run_local_smoke
- Approval persistence: false
- Scope: current process, one local smoke run only
- Max runs: 1
- Max backtests: 1
- Strategy Tester runs: 1
- Tournament run: blocked
- Backtest budget run: blocked
- Optimization: blocked
- Loop execution: blocked
- Close after run: required

## Template Intake Status

- Checked `_incoming/CLADE-template/`.
- Checked `_incoming/Copy of Website premium de laboratorio evolutivo de trading/`.
- Checked `design/templates/CLADE-template/`.
- Template files were not found locally.
- Created `frontend/templates/clade/` as the future intake target.
- No template JavaScript was executed.
- No frontend adapter was created yet.

## Next Step

Copy the premium template into one allowed intake path, then run a follow-up intake that imports static assets and creates the MT5 Robot Lab adapter.
