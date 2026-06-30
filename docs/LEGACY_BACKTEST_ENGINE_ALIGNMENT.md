# Legacy Backtest Engine Alignment

MVP-014E reviewed the failed one-run real MT5 smoke against the conceptual
contract used by the reference backtest engine. This review did not open,
copy or inspect the legacy repository. It used only the mission-provided
alignment checklist and the local private artifacts already produced by
MT5 Robot Lab.

## Current Failure

The latest real smoke attempt produced:

```text
exit_code=3294954941
report_file_found=false
parse_status=no_report_found
failure_stage=strategy_tester_failed_before_ea
```

The runner did create a private tester configuration with:

```text
[Tester]
Expert=Examples\MACD Sample
Symbol=XAUUSD
Period=M5
Optimization=0
Report=reports/private/real_mt5_smoke/<run_id>/strategy_tester_report
ReplaceReport=1
ShutdownTerminal=1
```

The private artifact boundary held: raw logs, local manifests and report
staging remained under `reports/private/real_mt5_smoke/`. Public summaries were
sanitized.

## Alignment Gap

The missing piece is not another blind retry. Before the next real smoke, the
runner must prove:

- terminal and MetaEditor readiness;
- exact Strategy Tester expert name;
- expected compiled EX5 location;
- private Strategy Tester report path;
- `ReplaceReport=1`;
- `ShutdownTerminal=1`;
- one-run smoke only;
- Operator Gate approval;
- close-after-run policy.

The previous failed attempt did not prove the expected compiled EX5. Because no
official report was emitted and no EA result was parsed, the failure is
classified as:

```text
strategy_tester_failed_before_ea
```

## Product Decision

MVP-014E adds a real MT5 preflight contract. Future real retry remains blocked
until the preflight returns:

```text
ready_for_real_retry=true
```

If the compiled EX5 path is missing, unresolved or outside the expected local
MT5 boundary, the retry must stop before launching MT5.

## Next Step

The next technical step is:

```text
MVP-014F - One-run Real Retry With Preflight
```

MVP-014F is still only one execution. It is not a tournament, not optimization,
not 10/50/100 backtests and not a product ranking run.
