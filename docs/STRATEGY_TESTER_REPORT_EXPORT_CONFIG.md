# Strategy Tester Report Export Configuration

MVP-014C defines the report export contract for the next real MT5 smoke. It
does not run MT5, does not launch Strategy Tester and does not execute an EA.

## Background

MVP-014B ran one gated real capture smoke, but no official Strategy Tester
report was captured. MVP-014C prepares the configuration and private artifact
boundary needed for the next one-run smoke to capture a parseable report.

## Required Tester Lines

Future generated tester configuration must include:

```text
[Tester]
Report=<private_report_base>
ReplaceReport=1
ShutdownTerminal=1
```

`Report` must point to a private run folder under:

```text
reports/private/real_mt5_smoke/<run_id>/
```

Raw reports must never target `reports/public`.

## Required Contract Fields

The report contract records:

- `run_id`
- `private_run_dir`
- `private_mt5_staging_dir`
- `report_base`
- `expected_report_html`
- `expected_report_xml`
- `expected_report_csv`
- `expected_log_dir`
- `report_required=true`
- `parse_required=true`
- `private_artifacts_only=true`
- `public_summary_sanitized=true`
- `replace_report=true`
- `shutdown_terminal=true`

The capture manifest also records:

- `report_export_configured`
- `report_capture_attempted`
- `report_capture_status`
- `parser_attempted`
- `parse_status`
- `mt5_close_policy`
- `mt5_close_attempted`
- `mt5_closed_after_run`

## Expected Report Candidates

The next smoke should search for:

- `.html`
- `.htm`
- `.xml`
- `.csv`
- `.json`

## Boundaries

- No real MT5 run in this MVP.
- No real backtest in this MVP.
- No Strategy Tester launch in this MVP.
- No EA execution in this MVP.
- No multi-run execution.
- No 10/50/100 backtest tournament.
- Raw reports remain private.
- Public summaries remain sanitized.
- MT5 must close after any future real execution.

Controlled multi-run remains blocked until a future one-run smoke captures and
parses an official Strategy Tester report.

## Next MVP

```text
MVP-014D One-run Real Report Capture Smoke
```

MVP-014D must use one real execution only, Operator Gate, close-after-run,
report export/capture enabled and parse enabled. It must not run a multi-run
tournament or 10/50/100 public backtests.
