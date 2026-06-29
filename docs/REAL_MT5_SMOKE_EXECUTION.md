# Real MT5 Smoke Execution

MVP-013C introduces the first controlled local MetaTrader 5 smoke execution path.
MVP-014B confirms that the one-run smoke worked at execution level, but official
Strategy Tester report capture is still not solved.

## Scope

This path is limited to:

- one local MT5 smoke attempt;
- one Strategy Tester request;
- one requested symbol and timeframe;
- no optimization;
- no tournament;
- no 100-backtest run;
- no stored credentials.
- MT5 close-after-run lifecycle recorded.

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
- `mt5_close_policy=always_after_real_run`.

Approving the real smoke also authorizes the app to close the MT5 instance it
started and controlled for that execution.

```text
Após a execução real, o MT5 será fechado para manter o ambiente limpo e evitar processos presos.
```

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

## MVP-014B Capture Status

The one-run capture smoke recorded:

- MT5 real run: true;
- Strategy Tester run: true;
- one run attempted;
- raw artifacts private;
- official report file found: false;
- parse status: no_report_found.

Future real runs must also record the MT5 close lifecycle fields:

```text
mt5_close_attempted
mt5_closed_after_run
mt5_close_method
mt5_close_error
mt5_process_owned_by_app
mt5_external_process_detected
manual_close_required
```

Controlled multi-run smoke remains blocked until report capture/export is fixed.

## Failure Policy

If the single run fails, the system records `HOLD_REAL_SMOKE_FAILED_NO_RETRY`.
The same mission must not retry automatically.

## CLI

The real smoke command is intentionally explicit:

```powershell
python app\mt5_robot_lab_app.py --run-real-mt5-smoke --operator-approval-phrase "Eu entendo que isso tentara apenas um smoke local do MT5"
```

This command is not used by CI.

## Next Required Fix

MVP-014C must define or correct the Strategy Tester report export configuration
before another real smoke is used to capture a parseable report.
