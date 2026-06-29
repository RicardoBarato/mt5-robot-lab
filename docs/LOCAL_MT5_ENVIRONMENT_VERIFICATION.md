# Local MT5 Environment Verification

MVP-013B verifies the local MetaTrader 5 environment without running a real
backtest.

## Command

```powershell
python app\mt5_robot_lab_app.py --detect-mt5-local
```

The command writes:

```text
reports/public/local_mt5_environment_status.json
reports/public/local_mt5_environment_status.md
```

## What It Detects

- `terminal64.exe`
- `metaeditor64.exe`
- safe MT5 readiness status
- common broker symbol mappings
- whether the Operator Gate is still required
- whether the environment is ready for a future one-run real smoke

## What It Does Not Do

- It does not launch MT5.
- It does not launch Strategy Tester.
- It does not run an EA.
- It does not run a real backtest.
- It does not start a tournament.
- It does not ask for broker login details.
- It does not store account, server or credential data.

## Output Fields

The public status artifacts include:

```text
mt5_detected
terminal_found
metaeditor_found
terminal_path_sanitized
metaeditor_path_sanitized
symbol_scan_mode
operator_gate_required
ready_for_real_smoke
mt5_real_run=false
backtest_real_run=false
strategy_tester_run=false
ea_executed=false
credentials_stored=false
```

## Readiness Rule

`ready_for_real_smoke=true` only means the local terminal and MetaEditor were
detected. It does not approve execution. The Operator Gate and explicit operator
approval remain mandatory.
