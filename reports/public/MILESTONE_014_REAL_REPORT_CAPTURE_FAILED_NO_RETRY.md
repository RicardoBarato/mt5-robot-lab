# Milestone 014 Real Report Capture - Failed No Retry

Status: `HOLD_MILESTONE_014_FAILED_NO_RETRY`

## Scope

Milestone 014 attempted to close the real MT5 run/report/parse loop:

```text
real MT5 smoke -> Strategy Tester -> report export -> capture -> parser -> sanitized summary
```

The milestone used one explicit Operator Gate approval and one real attempt only.
No second attempt was made.

## Execution Summary

- Operator Gate approved: true
- Real smoke attempted: true
- Real smoke runs: 1
- MT5 real run: true
- Strategy Tester run: true
- Backtest real run: false
- EA executed: false
- Tournament 100 run: false
- Smoke only: true
- Symbol: XAUUSD
- Timeframe: M5

## Failure Summary

- Result status: `failed_no_retry`
- Exit code: `3294954941`
- Failure reason: MT5 Strategy Tester smoke failed with exit code `3294954941`
- Report file found: false
- Parseable: false
- Parse status: `no_report_found`
- Metrics extracted: false

## Report Export Contract

- Report export configured: true
- Report target: private run folder
- ReplaceReport: true
- ShutdownTerminal: true
- Expected report candidates: html, htm, xml, csv, json
- Observed report files: none
- Observed log files: stdout.txt, stderr.txt

The observed logs are private artifacts. They are not copied into this public
summary.

## Close Policy

- MT5 close attempted: true
- MT5 closed after run: true
- Close method: `owned_process_already_closed`
- Manual close required: false

## Safety Boundary

- Raw artifacts private: true
- Public summary sanitized: true
- Credentials stored: false
- Private files committed: false
- Local raw paths published: false
- Real preset files committed: false
- Compiled EA binaries committed: false

## Next Decision

`review_failure_summary_before_retry`

Do not retry automatically. The next work should review the failure summary,
the generated tester configuration, and MT5/Strategy Tester launch mechanics
before any new explicit Operator Gate approval.
