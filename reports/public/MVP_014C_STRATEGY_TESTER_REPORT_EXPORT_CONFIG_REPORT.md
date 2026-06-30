# MVP-014C Strategy Tester Report Export Config Report

Status: report_export_contract_added

## Summary

MVP-014C adds a Strategy Tester report export contract for future gated real MT5
smoke runs.

## Contract

- Report export configured: true
- Report target: private run folder
- ReplaceReport: true
- ShutdownTerminal: true
- Report required: true
- Parse required: true
- Raw reports private only: true
- Public summary sanitized: true

## Tester Lines

```text
[Tester]
Report=<private_report_base>
ReplaceReport=1
ShutdownTerminal=1
```

## Expected Report Candidates

- `.html`
- `.htm`
- `.xml`
- `.csv`
- `.json`

## Safety Boundary

- MT5 real run: false
- Backtest real run: false
- Strategy Tester run: false
- EA executed: false
- Tournament 100 run: false
- Credentials stored: false
- Private files committed: false
- Paths sanitized: true

## Policy References

- Close MT5 after each future real execution: true
- Minimum public backtests: 10
- Default public backtests: 10
- Recommended options: 10, 50, 100
- One-run smoke: dev only and not for ranking

## Next MVP

MVP-014D One-run Real Report Capture Smoke.
