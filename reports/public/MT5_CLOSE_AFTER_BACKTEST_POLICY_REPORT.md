# MT5 Close After Backtest Policy Report

Status: policy_added_without_real_execution

## Summary

MT5 Robot Lab now has a documented close-after-real-run policy:

```text
mt5_close_policy=always_after_real_run
```

The implementation is designed to close only MT5 processes started and
controlled by the app. If an external MT5 process is detected, the summary must
record manual close as required instead of terminating the user's existing
session.

## Public Safety

- MT5 real run: false
- Backtest real run: false
- Strategy Tester run: false
- EA executed: false
- Tournament 100 run: false
- Credentials stored: false
- Private artifacts committed: false

## Required Fields

- `mt5_close_policy`
- `mt5_close_attempted`
- `mt5_closed_after_run`
- `mt5_close_method`
- `mt5_close_error`
- `mt5_process_owned_by_app`
- `mt5_external_process_detected`
- `manual_close_required`

## Operator Notice

Após a execução real, o MT5 será fechado para manter o ambiente limpo e evitar processos presos.
