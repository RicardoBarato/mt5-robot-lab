# MVP-014L One-Run Real Retry With Smoke EA

Status: HOLD_MVP_014L_REAL_RETRY_NO_REPORT_FOUND

## Operator Gate

- Operator gate approved: true
- Operator gate version: v2
- Approval method: cli_flag_one_run_local_smoke
- Approval persistent: false
- Smoke only: true
- Max backtests: 1
- Tournament 100 run: false

## Safe Smoke EA

- Expert: MT5RobotLab\SmokeHarness_Public
- Symbol: XAUUSD
- Timeframe: M5
- Strategy Tester run: true
- EA executed: true
- Exit code recorded: 0
- Exit code category: success

## Capture Result

- Report export configured: true
- Replace report: true
- Shutdown terminal: true
- Report capture attempted: true
- Report file found: false
- Parse enabled: true
- Parse status: no_report_found
- Result parseable: false
- Metrics extracted: false
- Failure stage: completed_report_pending_capture

## MT5 Close Policy

- MT5 close attempted: true
- MT5 closed after run: true
- MT5 close method: owned_process_already_closed
- Manual close required: false

## Security Boundary

- Raw artifacts private: true
- Public summary sanitized: true
- Paths sanitized: true
- Credentials stored: false
- Private files committed: false
- Preset artifacts committed: false
- Compiled binary artifacts committed: false

## Decision

The one-run real retry reached the Strategy Tester, executed the safe public smoke EA, and closed MT5 after the run. The official report file was not found, so no metrics were parsed.

Next decision: diagnose Strategy Tester report export/capture gap before any additional real smoke.
