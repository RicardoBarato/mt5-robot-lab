# Real MT5 Smoke Operator Gate

MVP-012 adds the explicit approval gate required before any future real local
MetaTrader 5 smoke execution.

This MVP does not run MT5, does not launch Strategy Tester and does not run a
real backtest.

## Why the Gate Exists

MT5 Robot Lab already has safe detection, dry-run smoke paths and public sample
artifacts. A future real smoke run is more sensitive because it may open the
local MT5 terminal and ask Strategy Tester to execute one local test.

The operator gate prevents accidental execution by requiring:

- explicit operator confirmation;
- exact approval phrase;
- MT5 detection readiness;
- smoke-only mode;
- exactly one max backtest;
- no 100-run tournament;
- no stored credentials.
- agreement that the app may close the MT5 instance started and controlled by
  the approved real run.

## Required Approval Phrase

Accepted English phrase:

```text
I understand this will attempt one local MT5 smoke run only
```

Accepted Portuguese phrase:

```text
Eu entendo que isso tentara apenas um smoke local do MT5
```

Close-after-run notice:

```text
Após a execução real, o MT5 será fechado para manter o ambiente limpo e evitar processos presos.
```

## Execution Classes

### Detection

Safe file and symbol diagnostics. Does not run MT5 and does not ask for
credentials.

### Smoke Stub

Safe local placeholder used by tests. Does not run Strategy Tester.

### Real Smoke

Future one-run MT5 Strategy Tester smoke. Requires this operator gate and a
separate human-reviewed MVP before execution.

### Real Backtest

Full Strategy Tester execution. Not enabled by MVP-012.

### Tournament

Multiple backtests or 100-run tournaments. Not enabled by MVP-012 and requires a
separate approval model.

## CLI Preview

Safe commands:

```powershell
python app\mt5_robot_lab_app.py --operator-gate-self-test
python app\mt5_robot_lab_app.py --preview-real-mt5-smoke-gate
```

These commands do not run MT5 and do not run Strategy Tester.

## Preview Outputs

Self-test preview output is written under ignored `runs/self_tests/` paths.
Reviewed public previews can be generated only by an explicit future command.

The preview keeps:

```text
mt5_real_run=false
backtest_real_run=false
execution_allowed=false
```

Approved real runs must also report:

```text
mt5_close_policy=always_after_real_run
manual_close_required=<true_or_false>
```

## Login Boundary

The user logs in inside MT5 if a broker or demo connection is required. The app
does not ask for credentials and does not store credentials.

## CI Boundary

CI must never run MT5 real execution. CI may run only the operator gate preview
and self-test.

CI must also keep the working tree clean after self-tests. Runtime artifacts from
self-tests belong in ignored folders, not in tracked `reports/public` files.

## Risk Disclosure

Backtests are research artifacts. A backtest is not a promise of profit and not
a financial recommendation.
