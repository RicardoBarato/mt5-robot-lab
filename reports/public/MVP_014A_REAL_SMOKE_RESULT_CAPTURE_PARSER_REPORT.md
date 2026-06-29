# MVP-014A Real Smoke Result Capture and Parser Report

## Executive Summary

MVP-014A adds a private result capture contract and a conservative Strategy Tester report parser for future one-run real MT5 smoke executions.

This mission did not run MT5, did not execute a backtest, did not start Strategy Tester and did not use a real MT5 report. Parser validation used synthetic fixtures only.

Readiness decision: READY_FOR_MVP014B_ONE_RUN_REAL_CAPTURE_SMOKE.

## Why MVP-014A Was Needed

MVP-013C proved that a gated one-run real smoke path can execute, but the project still needed a clean way to capture local artifacts and parse Strategy Tester outputs without leaking private paths, logs or broker/account details.

MVP-014A closes that gap by defining where a future real smoke stores local artifacts and how public-safe result extraction should behave.

## Result Capture Contract

The capture contract creates one ignored private folder per run under:

```text
reports/private/real_mt5_smoke/<run_id>/
```

Each run receives a local manifest:

```text
run_manifest.local.json
```

The manifest records only local run metadata, expected report file names, observed report file names, observed log file names, capture status and parse status. It does not publish raw local paths.

## Parser Scope

The parser accepts only explicitly provided report files. It does not scan drives, does not discover arbitrary files and can be constrained to an allowed root.

Supported initial formats:

```text
.html
.htm
.xml
.csv
.json
```

Extracted fields include:

```text
parseable
source_format
result_status
total_trades
net_profit
gross_profit
gross_loss
max_drawdown
initial_deposit
symbol
timeframe
started_at
ended_at
warnings
source_path_sanitized
```

Unknown, missing or unsupported fields are reported conservatively as `None` or `unsupported_format_or_missing_fields`.

## Synthetic Fixture Policy

MVP-014A uses synthetic Strategy Tester fixtures only. The fixtures are small test files created for parser validation and do not contain live, demo, broker, account, server or raw MT5 report data.

Synthetic parse status: parseable.

Real parse status: not attempted.

## Private Artifacts Boundary

Raw future MT5 outputs remain private by default. The public report created by this mission contains only the contract and parser summary.

The mission does not commit:

```text
reports/private/
runs/
MetaTrader preset files
compiled Expert Advisor binaries
raw log files
terminal journal files
environment files
credentials
raw broker/account data
```

## What Is Still Not Confirmed

MVP-014A does not confirm the exact report file emitted by the local Strategy Tester after a new real smoke execution.

It also does not confirm that a real report is parseable. That requires MVP-014B, where one explicit Operator Gate run should create a new private report and then parse that specific file once.

## Readiness For MVP-014B

READY_FOR_MVP014B_ONE_RUN_REAL_CAPTURE_SMOKE

MVP-014B should execute exactly one gated real smoke, capture the raw report under the private run folder, parse the explicitly identified report file and publish only sanitized metrics.
