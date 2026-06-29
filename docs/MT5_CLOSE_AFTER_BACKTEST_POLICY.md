# MT5 Close After Backtest Policy

MT5 Robot Lab must close the MetaTrader 5 terminal instance it starts for every
future gated real run.

## Policy

```text
mt5_close_policy=always_after_real_run
```

After a real smoke or real backtest attempt, the runner must record:

- `mt5_close_policy`;
- `mt5_close_attempted`;
- `mt5_closed_after_run`;
- `mt5_close_method`;
- `mt5_close_error`;
- `mt5_process_owned_by_app`;
- `mt5_external_process_detected`;
- `manual_close_required`.

## Operator Gate Text

Approving a real smoke or real backtest also authorizes MT5 Robot Lab to close
the MT5 terminal instance that was started and controlled by that execution.

```text
Após a execução real, o MT5 será fechado para manter o ambiente limpo e evitar processos presos.
```

## External Terminal Boundary

If MT5 was already open and was not started by MT5 Robot Lab, the app must not
terminate that external user session automatically. The run summary must record:

```text
mt5_external_process_detected=true
manual_close_required=true
```

## Failure Boundary

The close lifecycle must be recorded even when:

- the Strategy Tester run succeeds;
- the Strategy Tester run fails;
- MT5 exits with a non-zero code;
- the run times out;
- no report is found;
- the parser cannot parse a report.

## Current Mission Boundary

This policy adds code, docs and tests only. It does not run MT5, does not run
Strategy Tester, does not execute an EA and does not start a tournament.
