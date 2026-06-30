# Roadmap

1. Bootstrap desktop scaffold. [completed]
2. Implement MT5 detection UI. [completed]
3. Add real MT5 adapter smoke controls. [completed]
4. Connect `ea-xau` as first lab. [completed as registry/config foundation]
5. Add Champion DNA views and records. [completed as public-safe MVP records]
6. Add robust exports and submission packages. [completed as samples/specs]
7. Execute gated one-run MT5 smoke. [completed]
8. Add result capture/parser contract. [completed]
9. Execute one-run capture smoke. [completed: failed no retry]
10. Add backtest budget product policy. [completed]
11. Diagnose real MT5 report-capture failure and add preflight. [completed]
12. Add safe retry preflight readiness command. [completed]
13. Retry one-run real smoke only after preflight review and Operator Gate approval. [completed: blocked before launch]
14. Add runtime preflight marker handoff dry-run. [completed]
15. Retry one-run real smoke only after runtime dry-run proof and Operator Gate approval. [completed: EA not executed, no retry]
16. Diagnose runtime versus terminal execution gap before any new retry. [completed]
17. Verify terminal DataDir EX5 and Strategy Tester contract before any new retry. [completed: retry blocked]
18. Retry one-run real smoke only after terminal contract audit passes. [recommended next]
19. Add installer and portable package after release review. [future]

## Current Stage

PROJECT_STAGE = advanced_technical_mvp_not_final_product

REAL_MT5_STATUS = terminal_contract_audit_blocks_retry_until_ex5_datadir_mapping_proven

NEXT_REQUIRED_STEP = MVP_014L_one_run_real_retry_only_after_terminal_contract_audit_passes

BACKTEST_BUDGET_POLICY = minimum_public_backtests_10_default_10_unified_ranking

## Recent MVP Status

| MVP | Status | Notes |
| --- | --- | --- |
| MVP-013C | completed_or_in_pr | First gated one-run real MT5 smoke executed. |
| MVP-013D | completed_or_reviewed | Real smoke result reviewed and documented. |
| MVP-014A | completed | Capture contract and conservative parser merged. |
| MVP-014B | completed_no_report_found | One real capture smoke ran, but no official Strategy Tester report was found. |
| Policy | completed | Public minimum is 10 backtests, default is 10, options are 10/50/100 and ranking is unified. |
| MVP-014C | completed_in_pr | Defines Strategy Tester report export before any multi-run smoke. |
| MVP-014D | failed_no_retry | One real report capture smoke was attempted once and failed with sanitized exit-code evidence. |
| MVP-014E | completed | Failure diagnosis, legacy alignment notes and preflight blocker added. |
| MVP-014F | completed | Safe preflight readiness command and public summaries added. |
| MVP-014G | completed_not_parseable | Retry command blocked before terminal launch because runtime preflight did not receive the accepted readiness marker. |
| MVP-014H | completed | Runtime contract and dry-run attach the accepted readiness marker into runtime preflight. |
| MVP-014I | blocked_strategy_tester_failed_before_ea | One-run real retry reached Strategy Tester launch but failed before EA execution; no retry was attempted. |
| MVP-014J | completed | Diagnosed runtime versus terminal gap without launching MT5. |
| MVP-014K | blocked_terminal_contract | Terminal DataDir EX5 contract audit added; retry remains blocked. |
| MVP-014L | recommended_next_after_terminal_contract_pass | One-run real retry only after terminal contract audit PASS. |

## Backtest Budget Policy

- Minimum public backtests: 10.
- Default backtests: 10.
- Recommended options: 10, 50, 100.
- Custom backtests: allowed with minimum 10.
- Ranking mode: single unified ranking.
- Transparency fields: `backtests_requested`, `backtests_completed`,
  `search_budget`, `generation_id`, `candidate_id`.
- Execution: sequential only, `max_concurrent_mt5=1`.
- MT5 close policy: close after each backtest.
- Internal one-run smoke: dev only, not for ranking and not for product claims.

## MVP-014C Scope

Title: MVP-014C - MT5 Strategy Tester Report Export Configuration

Objective: Fix or define how MT5 Strategy Tester should export official reports
so that the next one-run real smoke can capture a parseable report.

MVP-014C must not start a tournament, must not run 100 backtests and must remain
behind explicit Operator Gate controls for any real smoke retry.

## MVP-014D Result

Title: MVP-014D - One-run Real Report Capture Smoke

Result: one gated real smoke was attempted with report export/capture enabled.
The Strategy Tester process returned exit code `3294954941`, no official report
was found and no retry was attempted.

Next decision: review the failure summary before approving any retry.

## MVP-014E Result

Title: MVP-014E - Real MT5 Failure Diagnosis and Legacy Runner Alignment

Result: the failure was classified as
`strategy_tester_failed_before_ea`. The previous run had
`exit_code=3294954941`, no official report and no parsed EA result. MVP-014E
added a preflight validator for terminal, MetaEditor, expert path, expected
compiled EX5, private report contract, tester INI flags and close-after-run
policy.

Next decision: run MVP-014F preflight readiness without MT5 execution.

## MVP-014F Result

Title: MVP-014F - Preflight Readiness

Result: added `python app\mt5_robot_lab_app.py --real-mt5-preflight`. The command
writes sanitized public preflight summaries, does not launch MT5, does not start
Strategy Tester and does not execute an EA.

Next decision: the operator may approve `MVP-014G - One-run Real Retry After
Preflight` only after reviewing the preflight summaries.

## MVP-014G Result

Title: MVP-014G - One-run Real Retry After Preflight

Result: the Operator Gate was approved and the non-executing preflight passed
with `ready_for_retry=true`, but the real-run runtime preflight blocked before
launching MT5 with `compiled_ex5_not_configured`. No Strategy Tester process was
started, no EA executed and no report was captured.

Next decision: run `MVP-014H - Runtime Gap Diagnosis` before requesting any
new real retry approval.

## MVP-014H Result

Title: MVP-014H - Runtime Preflight Marker Handoff Diagnosis

Result: diagnosed the root cause as
`compiled_ex5_ready_but_not_attached_to_runtime`. The safe preflight accepted
the local readiness marker, but the real-run runtime preflight previously built
its config from a different object that did not include the expected compiled
artifact path. MVP-014H adds an explicit runtime contract and a non-executing
`--real-mt5-runtime-dry-run` command.

Next decision: `MVP-014I - One-run Real Retry With Runtime Dry-Run Proven` may
be requested only after `--real-mt5-preflight`, `--real-mt5-runtime-dry-run`, a
clean worktree and fresh Operator Gate approval.

## MVP-014I Result

Title: MVP-014I - One-run Real Retry With Runtime Dry-Run Proven

Result: the Operator Gate was approved, the safe preflight passed and the
runtime dry-run passed. One real local MT5 smoke was attempted. The run reached
the Strategy Tester launch path, but the EA did not execute and no official
report was captured.

```text
real_smoke_attempted=true
real_smoke_runs=1
mt5_real_run=true
strategy_tester_run=true
backtest_real_run=false
ea_executed=false
report_file_found=false
parse_status=no_report_found
failure_stage=strategy_tester_failed_before_ea
exit_code=3294954941
mt5_closed_after_run=true
```

Next decision: do not retry immediately. Run `MVP-014J - Runtime vs Terminal
Gap Diagnosis` before any new real attempt.

## MVP-014J Result

Title: MVP-014J - Runtime vs Terminal Gap Diagnosis

Result: added `python app\mt5_robot_lab_app.py --terminal-runtime-diagnostics`.
The command reviews local private run artifacts and writes only sanitized public
diagnostic summaries. It does not launch MT5, does not start Strategy Tester and
does not execute an EA.

```text
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
```

Next decision: `MVP-014K - Terminal DataDir EX5 Verification` must prove the
terminal DataDir and Strategy Tester expert mapping before any new retry.

## MVP-014K Result

Title: MVP-014K - Terminal DataDir EX5 Verification

Result: added `python app\mt5_robot_lab_app.py --terminal-contract-audit`. The
command is non-executing and writes sanitized public summaries. It does not
launch MT5, start Strategy Tester, compile an EX5 or execute an EA.

```text
terminal_contract_audit=FAIL
compiled_ex5_verified_in_terminal_datadir=false
terminal_datadir_consistent=false
expert_mapping_valid_for_tester=false
tester_ini_contract_ready=false
report_contract_ready=true
close_after_run_ready=true
ready_for_real_retry=false
```

Blocking issues:

```text
terminal_data_dir_missing
compiled_ex5_readiness_marker_missing
compiled_ex5_not_found_in_terminal_datadir
compiled_ex5_not_verified_in_terminal_datadir
expert_mapping_invalid_for_strategy_tester
```

Next decision: fix the terminal DataDir EX5 contract. Only after
`--terminal-contract-audit` returns PASS can the operator approve
`MVP-014L - One-run Real Retry With Terminal Contract Audit PASS`.
