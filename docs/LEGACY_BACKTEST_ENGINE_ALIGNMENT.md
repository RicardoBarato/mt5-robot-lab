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

MVP-014F added the non-executing preflight readiness command:

```text
python app\mt5_robot_lab_app.py --real-mt5-preflight
```

MVP-014H added the matching runtime contract dry-run:

```text
python app\mt5_robot_lab_app.py --real-mt5-runtime-dry-run
```

This closes the handoff gap where the preflight readiness marker was accepted
but not attached to the real-run runtime config. The next real execution step is
`MVP-014I - One-run Real Retry With Runtime Dry-Run Proven`.

MVP-014I is still only one execution. It is not a tournament, not optimization,
not 10/50/100 backtests and not a product ranking run.

## MVP-014I Result

MVP-014I executed exactly one retry after the preflight and runtime dry-run
passed. The result did not close the loop: Strategy Tester launch was reached,
but the EA did not execute and no official report was captured.

```text
failure_stage=strategy_tester_failed_before_ea
exit_code=3294954941
report_file_found=false
parse_status=no_report_found
mt5_closed_after_run=true
```

## MVP-014J Result

MVP-014J added a non-executing diagnostic command:

```text
python app\mt5_robot_lab_app.py --terminal-runtime-diagnostics
```

The diagnostic reviews local private run artifacts and publishes only sanitized
conclusions. It found the current root cause:

```text
root_cause=compiled_ex5_marker_not_verified_in_terminal_datadir
exit_code=3294954941
failure_stage=strategy_tester_failed_before_ea
ready_for_real_retry=false
```

## MVP-014K Result

MVP-014K added the terminal DataDir EX5 verification command:

```text
python app\mt5_robot_lab_app.py --terminal-contract-audit
```

The command is non-executing and currently blocks another retry:

```text
terminal_contract_audit=FAIL
compiled_ex5_verified_in_terminal_datadir=false
terminal_datadir_consistent=false
expert_mapping_valid_for_tester=false
ready_for_real_retry=false
```

The next alignment task is to make the terminal contract pass. `MVP-014L
One-run Real Retry With Terminal Contract Audit PASS` is blocked until the
terminal DataDir and Strategy Tester expert mapping are proven.
