# MVP-014F Preflight Readiness

- Status: blocked_preflight_failed
- Ready for retry: false
- Blocking issues: compiled_ex5_readiness_marker_missing, terminal_data_dir_mismatch, compiled_ex5_not_found_in_terminal_datadir, compiled_ex5_not_verified_in_terminal_datadir, expert_mapping_invalid_for_strategy_tester
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
