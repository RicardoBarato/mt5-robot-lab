# Real MT5 Smoke Execution

MVP-013C introduced the first controlled local MetaTrader 5 smoke execution
path. MVP-014B confirmed that the one-run smoke worked at execution level, but
official Strategy Tester report capture was not solved. MVP-014D then attempted
one report-capture smoke and failed without retry.

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
- preflight status is ready;
- expected expert path is checked;
- expected compiled EX5 is checked;
- Strategy Tester report path is private;
- report export contract is valid.

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

## MVP-014D Failure and MVP-014E Preflight

MVP-014D recorded:

```text
exit_code=3294954941
failure_stage=strategy_tester_failed_before_ea
report_file_found=false
parse_status=no_report_found
```

MVP-014E adds a preflight validator. Any retry must stop before launching MT5
unless the validator confirms terminal readiness, MetaEditor readiness, expert
path, expected compiled EX5, private report path, tester INI flags,
Operator Gate approval and close-after-run policy.

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

MVP-014C defined the Strategy Tester report export configuration. Future
generated tester config must include:

```text
[Tester]
Report=<private_report_base>
ReplaceReport=1
ShutdownTerminal=1
```

MVP-014F adds `python app\mt5_robot_lab_app.py --real-mt5-preflight` for a
safe, non-executing readiness check.

MVP-014G received fresh Operator Gate approval and passed the non-executing
preflight, but the real-run runtime preflight blocked before terminal launch
with `compiled_ex5_not_configured`. No MT5 real run, Strategy Tester run or EA
execution occurred in MVP-014G.

The next step is `MVP-014H Runtime Gap Diagnosis`, focused on the handoff
between the accepted preflight readiness marker and the runtime smoke path.

MVP-014H adds a runtime contract and a safe dry-run:

```powershell
python app\mt5_robot_lab_app.py --real-mt5-runtime-dry-run
```

The root cause was `compiled_ex5_ready_but_not_attached_to_runtime`: the
accepted readiness marker existed, but the real-run preflight read a runtime
configuration that did not carry it. The next real retry is `MVP-014I` and must
be preceded by both `--real-mt5-preflight` and `--real-mt5-runtime-dry-run`.
