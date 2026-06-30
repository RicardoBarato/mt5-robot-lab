# MVP Queue 001

The Grand MVP queue tracks the current public-safe desktop product roadmap.

| ID | Title | Priority | Status |
| --- | --- | --- | --- |
| MVP-001 | Desktop Navigation v2 | P0 | completed |
| MVP-002 | Tournament Config Wizard | P0 | completed |
| MVP-003 | MT5 Detection Real Smoke | P1 | completed |
| MVP-004 | Symbol Discovery Adapter | P1 | completed |
| MVP-005 | Local Mutation Engine Dry-Run | P1 | completed |
| MVP-006 | Champion DNA v1 / smoke package | P1 | completed |
| MVP-007 | Risk Profile Ranking Engine | P1 | completed |
| MVP-008 | Champion DNA v2 | P1 | completed |
| MVP-009 | Submission Package v1 | P2 | completed |
| MVP-010 | Online Leaderboard Spec | P3 | completed |
| MVP-011 | Licensing and Contribution Policy | P2 | completed |
| MVP-012 | Real MT5 Smoke Operator Gate | high | completed |
| MVP-013C | One-run Real MT5 Smoke Execution | high | completed_or_in_pr |
| MVP-013D | Real Smoke Result Review | high | completed_or_reviewed |
| MVP-014A | Real Smoke Result Capture and Parser | high | completed |
| MVP-014B | One-run Real Capture Smoke | high | completed_no_report_found |
| Hardening | MT5 Close After Real Run Policy | high | completed |
| Policy | Backtest Budget Product Policy | high | completed |
| MVP-014C | MT5 Strategy Tester Report Export Configuration | high | completed_in_pr |
| MVP-014D | One-run Real Report Capture Smoke | high | failed_no_retry |
| MVP-014E | Real MT5 Failure Diagnosis and Legacy Runner Alignment | high | completed |
| MVP-014F | Preflight Readiness | high | completed |
| MVP-014G | One-run Real Retry After Preflight | high | completed_not_parseable |
| MVP-014H | Runtime Gap Diagnosis | high | completed |
| MVP-014I | One-run Real Retry With Runtime Dry-Run Proven | high | blocked_strategy_tester_failed_before_ea |
| MVP-014J | Runtime vs Terminal Gap Diagnosis | high | completed |
| MVP-014K | Terminal DataDir EX5 Verification | high | blocked_terminal_contract |
| MVP-014K2 | Terminal DataDir and EX5 Readiness Bootstrap | high | hold_ex5_not_found_in_terminal_datadir |
| MVP-014L | One-run Real Retry With Terminal Contract Audit PASS | high | blocked_until_terminal_contract_pass |

Use:

```powershell
python factory\mvp_factory.py --list
python factory\mvp_factory.py --next
python factory\mvp_factory.py --generate-prompt MVP-012
```

The initial 10-MVP queue was completed after `MVP-010 Online Leaderboard Spec`.
MVP-011 extends the queue with licensing, brand, contribution, submission and
official ranking governance. MVP-012 adds explicit approval gates for real MT5
smoke execution.

MVP-013C executed a gated one-run local MT5 smoke. MVP-014A added the private
capture contract and conservative parser. MVP-014B ran one capture smoke and
recorded `no_report_found` because no official Strategy Tester report was
captured.

The next technical step is to place or compile the expected EX5 inside the
resolved terminal DataDir without running MT5 or a backtest. `MVP-014L One-run
Real Retry With Terminal Contract Audit PASS` remains blocked until `MVP-014K2`
proves the terminal DataDir, compiled EX5 and Strategy Tester expert mapping
contract.

Before MVP-014D, every real execution path must carry the close-after-run
policy:

```text
mt5_close_policy=always_after_real_run
```

Após a execução real, o MT5 será fechado para manter o ambiente limpo e evitar processos presos.

The public product budget policy is:

```text
minimum_public_backtests=10
default_backtests=10
recommended_options=10,50,100
custom_backtests_allowed=true
custom_backtests_minimum=10
ranking_mode=single_unified_ranking
sequential_only=true
max_concurrent_mt5=1
close_mt5_after_each_backtest=true
```

One-run smoke remains internal/dev only and is not valid for ranking or product
claims. Every ranking result must disclose `backtests_requested`,
`backtests_completed`, `search_budget`, `generation_id` and `candidate_id`.

MVP-014C completed objective:

```text
Fix or define how MT5 Strategy Tester should export official reports so that
the next one-run real smoke can capture a parseable report.
```

MVP-014D must remain:

```text
1 execution real
Operator Gate required
close-after-run required
report export/capture enabled
parse enabled
no multi-run
no tournament
no 10/50/100 public backtests yet
```

MVP-014D result:

```text
real_smoke_attempted=true
real_smoke_runs=1
result_status=failed_no_retry
exit_code=3294954941
report_file_found=false
parse_status=no_report_found
next_decision=review_failure_summary_before_retry
```

MVP-014E result:

```text
failure_stage=strategy_tester_failed_before_ea
exit_code=3294954941
preflight_validator_added=true
expert_path_checked=true
compiled_ex5_checked=true
report_export_contract_checked=true
report_path_privacy_checked=true
ready_for_retry=false
next_mvp=MVP-014F One-run Real Retry With Preflight
```

MVP-014F result:

```text
preflight_command=true
ready_for_retry=true
blocking_issues=none
mt5_real_run_new=false
backtest_real_run_new=false
strategy_tester_run_new=false
ea_executed_new=false
next_mvp=MVP-014G One-run Real Retry After Preflight
```

MVP-014G result:

```text
operator_gate_approved=true
preflight_before_run=PASS
ready_for_retry_before_run=true
ex5_readiness_accepted=true
real_smoke_attempted=false
real_smoke_runs=0
mt5_real_run=false
strategy_tester_run=false
ea_executed=false
failure_stage=runtime_preflight_failed_before_terminal_launch
preflight_blocking_issue=compiled_ex5_not_configured
next_mvp=MVP-014H Runtime Gap Diagnosis
```

MVP-014H result:

```text
root_cause=compiled_ex5_ready_but_not_attached_to_runtime
runtime_contract_created=true
ex5_marker_attached_to_runtime=true
compiled_ex5_configured_in_dry_run=true
preflight_command=PASS
runtime_dry_run_command=PASS
mt5_real_run_new=false
strategy_tester_run_new=false
ea_executed_new=false
next_mvp=MVP-014I One-run Real Retry With Runtime Dry-Run Proven
```

MVP-014I result:

```text
operator_gate_approved=true
preflight_before_run=PASS
runtime_dry_run_before_run=PASS
ready_for_real_retry=true
blocking_issues=none
ex5_marker_attached_to_runtime=true
compiled_ex5_configured_in_dry_run=true
real_smoke_attempted=true
real_smoke_runs=1
mt5_real_run=true
strategy_tester_run=true
backtest_real_run=false
ea_executed=false
report_file_found=false
result_parseable=false
parse_status=no_report_found
failure_stage=strategy_tester_failed_before_ea
exit_code=3294954941
mt5_closed_after_run=true
next_mvp=MVP-014J Runtime vs Terminal Gap Diagnosis
```

MVP-014J result:

```text
terminal_runtime_diagnostics_command=PASS
root_cause=compiled_ex5_marker_not_verified_in_terminal_datadir
exit_code=3294954941
failure_stage=strategy_tester_failed_before_ea
tester_ini_reviewed=true
expert_mapping_checked=true
data_dir_consistency_checked=true
report_contract_checked=true
terminal_args_checked=true
contract_bug_fixed=false
ready_for_real_retry=false
mt5_real_run_new=false
strategy_tester_run_new=false
ea_executed_new=false
next_mvp=MVP-014K One-run Real Retry only after terminal contract diagnosis passes
```

MVP-014K result:

```text
terminal_contract_audit_command=PASS
terminal_contract_audit=FAIL
compiled_ex5_verified_in_terminal_datadir=false
terminal_datadir_consistent=false
expert_mapping_valid_for_tester=false
tester_ini_contract_ready=false
report_contract_ready=true
close_after_run_ready=true
ready_for_real_retry=false
blocking_issues=terminal_data_dir_missing,compiled_ex5_readiness_marker_missing,compiled_ex5_not_found_in_terminal_datadir,compiled_ex5_not_verified_in_terminal_datadir,expert_mapping_invalid_for_strategy_tester
mt5_real_run_new=false
strategy_tester_run_new=false
ea_executed_new=false
next_mvp=MVP-014L One-run Real Retry With Terminal Contract Audit PASS
```

MVP-014K2 result:

```text
compiled_ex5_readiness_bootstrap=HOLD
terminal_data_dir_found=true
datadir_source=appdata_origin_txt
compiled_ex5_found_in_terminal_datadir=false
compiled_ex5_marker_created=false
compiled_ex5_verified_in_terminal_datadir=false
terminal_datadir_consistent=false
expert_mapping_valid_for_tester=false
tester_ini_contract_ready=false
report_contract_ready=true
close_after_run_ready=true
ready_for_real_retry=false
blocking_issues=compiled_ex5_readiness_marker_missing,terminal_data_dir_mismatch,compiled_ex5_not_found_in_terminal_datadir,compiled_ex5_not_verified_in_terminal_datadir,expert_mapping_invalid_for_strategy_tester
mt5_real_run_new=false
strategy_tester_run_new=false
ea_executed_new=false
next_step=compile_or_copy_ex5_to_terminal_datadir_before_retry
```
