# Real MT5 Report Capture Summary

Status: `failed_no_retry`

## Result

- Real smoke attempted: true
- Runs attempted: 1
- MT5 real run: true
- Strategy Tester run: true
- Backtest real run: false
- EA executed: false
- Tournament 100 run: false
- Exit code: `3294954941`
- Failure reason: MT5 Strategy Tester smoke failed with exit code `3294954941`

## Report Capture

- Report export enabled: true
- ReplaceReport: true
- ShutdownTerminal: true
- Report file found: false
- Parseable: false
- Parse status: `no_report_found`
- Metrics extracted: false

## Safety

- MT5 close attempted: true
- MT5 closed after run: true
- Raw artifacts private: true
- Public summary sanitized: true
- Credentials stored: false
- Private files committed: false
- Paths sanitized: true

## Decision

Next decision: `review_failure_summary_before_retry`

Do not retry automatically. Review the sanitized failure summary and private
artifact boundary before approving any future real MT5 attempt.
