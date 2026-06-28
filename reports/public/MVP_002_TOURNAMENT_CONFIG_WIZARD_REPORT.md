# MVP-002 Tournament Config Wizard Report

## Objective

Implement the second Grand MVP from the factory queue: a safe tournament
configuration model, validation rules, wizard state, public dry-run preview,
tests, docs and MVP status tracking.

## Files Changed

- `app/core/tournament_config.py`
- `app/mt5_robot_lab_app.py`
- `app/ui/main_window.py`
- `app/ui/screens.py`
- `.gitignore`
- `config/tournament.example.json`
- `docs/TOURNAMENT_CONFIG_WIZARD.md`
- `docs/USER_FLOW_DESKTOP.md`
- `docs/DESKTOP_UI_DIRECTION.md`
- `docs/MVP_QUEUE_001.md`
- `README.md`
- `tests/test_tournament_config.py`
- `factory/mvp_queue.json`
- `factory/mvp_status.json`

## Wizard Fields

- lab
- symbol
- timeframe
- years
- balance
- max backtests
- champion count
- intelligence mode
- outputs
- MT5 terminal path placeholder
- MT5 MetaEditor path placeholder

## Validations

- positive numeric values;
- `champion_count <= max_backtests`;
- supported timeframe;
- supported intelligence mode;
- supported output formats;
- public summary excludes secrets and sensitive local paths.

## Tests Run

Final validation is recorded in the mission closeout.

## Scope Confirmations

- MT5 real run did not execute.
- Real backtest did not execute.
- 100-run tournament did not start.
- `ea-xau` was not touched.
- PayoffGrid was not touched.
- ONPN11 was not touched.
- No private files were copied.

## Next MVP

MVP-003 MT5 Detection Real Smoke.
