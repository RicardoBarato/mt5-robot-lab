# Real MT5 Smoke Execution

MVP-013C introduces the first controlled local MetaTrader 5 smoke execution path.

## Scope

This path is limited to:

- one local MT5 smoke attempt;
- one Strategy Tester request;
- one requested symbol and timeframe;
- no optimization;
- no tournament;
- no 100-backtest run;
- no stored credentials.

## Operator Gate

Execution requires one exact approval phrase:

```text
I understand this will attempt one local MT5 smoke run only
```

or:

```text
Eu entendo que isso tentara apenas um smoke local do MT5
```

The runner must also confirm:

- MT5 detected;
- `terminal64.exe` found;
- `metaeditor64.exe` found;
- `max_backtests=1`;
- `smoke_only=true`;
- `tournament_100_run=false`;
- `credentials_stored=false`.

## Artifact Boundary

Raw local artifacts must stay under:

```text
reports/private/real_mt5_smoke/
```

Public summaries may be written to:

```text
reports/public/real_mt5_smoke_summary.json
reports/public/real_mt5_smoke_summary.md
```

Public summaries must not include local paths, broker login details,
credentials, raw logs, real presets or compiled EA binaries.

## Failure Policy

If the single run fails, the system records `HOLD_REAL_SMOKE_FAILED_NO_RETRY`.
The same mission must not retry automatically.

## CLI

The real smoke command is intentionally explicit:

```powershell
python app\mt5_robot_lab_app.py --run-real-mt5-smoke --operator-approval-phrase "Eu entendo que isso tentara apenas um smoke local do MT5"
```

This command is not used by CI.
