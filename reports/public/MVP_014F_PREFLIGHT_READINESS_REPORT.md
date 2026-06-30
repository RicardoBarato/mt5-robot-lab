# MVP-014F Preflight Readiness

- Status: ready_for_one_run_retry
- Ready for retry: true
- Blocking issues: none
- Warnings: none
- Expert path ready: true
- Compiled EX5 ready: true
- Tester INI contract ready: true
- Report contract ready: true
- Close-after-run ready: true
- Operator Gate ready: true
- MT5 real run new: false
- Backtest real run new: false
- Strategy Tester run new: false
- EA executed new: false
- Tournament 100 run: false
- Credentials stored: false
- Paths sanitized: true

This preflight does not launch MT5, does not start Strategy Tester and does not execute an EA.
The EX5 readiness check uses an ignored local readiness marker under runs/ and must be rechecked before any real retry.
