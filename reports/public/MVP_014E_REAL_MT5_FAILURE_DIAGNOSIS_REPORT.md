# MVP-014E Real MT5 Failure Diagnosis

Status: completed.

MVP-014E diagnosed the failed one-run real MT5 report capture without running a
new MT5 attempt.

## Reviewed Local Artifacts

Private artifacts were reviewed locally only under the ignored real smoke run
folder. No private raw report, log, preset artifact, compiled artifact or local path was
copied into public outputs.

The previous run recorded:

```text
exit_code=3294954941
capture_status=no_report_found
parse_status=no_report_found
observed_report_files=[]
observed_log_files=stdout.txt,stderr.txt
report_export_configured=true
replace_report=true
shutdown_terminal=true
```

## Diagnosis

The generated tester configuration contained a Strategy Tester section, report
export path and close-after-run controls. The remaining critical gap is that the
runner did not preflight the exact expected compiled EX5 before launch.

The failure is classified as:

```text
failure_stage=strategy_tester_failed_before_ea
exit_code_category=unknown_terminal_exit
```

This classification is conservative: the process returned a nonzero code, no
official Strategy Tester report appeared, and no EA result was parsed.

## Changes Added

- Added `app/core/real_mt5_preflight.py`.
- Added preflight checks for terminal, MetaEditor, expert path, expected
  compiled EX5, symbol, period, tester INI, report contract and private paths.
- Added failure-stage and exit-code fields to runner/capture summaries.
- Added public-safe docs and this report.

## Retry Policy

Retry is not approved by this mission.

```text
ready_for_real_retry=false
next_mvp=MVP-014F One-run Real Retry With Preflight
```

MVP-014F may proceed only with explicit Operator Gate approval and preflight
success. It remains limited to one real attempt.

## Boundaries

```text
mt5_real_run_new=false
backtest_real_run_new=false
strategy_tester_run_new=false
ea_executed_new=false
tournament_100_run=false
credentials_stored=false
private_files_committed=false
paths_sanitized=true
```
