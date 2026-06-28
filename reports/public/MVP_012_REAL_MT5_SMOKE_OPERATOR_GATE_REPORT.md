# MVP-012 Real MT5 Smoke Operator Gate Report

## Objective

Create explicit operator approval gates for future real MT5 smoke execution
without running MT5 by default.

## Files Added or Updated

- `app/core/operator_gate.py`
- `app/core/mt5_runner.py`
- `app/core/candidate_runner.py`
- `app/mt5_robot_lab_app.py`
- `app/ui/screens.py`
- `app/ui/main_window.py`
- `tests/test_operator_gate.py`
- `docs/REAL_MT5_SMOKE_OPERATOR_GATE.md`
- `docs/REAL_MT5_EXECUTION_BOUNDARY.md`
- `reports/public/operator_gate_preview.json`
- `reports/public/operator_gate_preview.md`

## Gate Conditions

Real smoke execution is allowed only when the operator phrase matches, MT5
diagnostics are ready, smoke-only mode is true, max backtests equals 1, 100-run
tournament mode is false and no credentials are stored.

## Runner Boundary

If a caller requests real execution without an approved gate, the runner returns:

```text
blocked_by_operator_gate
```

No subprocess is launched in that path.

## CLI Commands

```powershell
python app\mt5_robot_lab_app.py --operator-gate-self-test
python app\mt5_robot_lab_app.py --preview-real-mt5-smoke-gate
```

Both commands are safe previews and do not execute MT5.

## Limitations

- No MT5 real run was performed.
- No Strategy Tester run was performed.
- No real backtest was performed.
- No 100-run tournament was performed.
- No credentials were stored.
- No `.exe`, `.zip`, release or tag was created.

## Next MVP

Recommended next MVP after human review: `MVP-013 Real MT5 Smoke Execution`.
