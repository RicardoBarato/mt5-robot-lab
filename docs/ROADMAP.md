# Roadmap

1. Bootstrap desktop scaffold. [completed]
2. Implement MT5 detection UI. [completed]
3. Add real MT5 adapter smoke controls. [completed]
4. Connect `ea-xau` as first lab. [completed as registry/config foundation]
5. Add Champion DNA views and records. [completed as public-safe MVP records]
6. Add robust exports and submission packages. [completed as samples/specs]
7. Execute gated one-run MT5 smoke. [completed]
8. Add result capture/parser contract. [completed]
9. Execute one-run capture smoke. [in PR: no official report captured]
10. Add backtest budget product policy. [completed]
11. Fix Strategy Tester report export/capture. [recommended next]
12. Add installer and portable package after release review. [future]

## Current Stage

PROJECT_STAGE = advanced_technical_mvp_not_final_product

REAL_MT5_STATUS = one_run_smoke_completed_no_report_captured

NEXT_REQUIRED_STEP = mvp_014d_one_run_real_report_capture_smoke

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
| MVP-014D | recommended_next | One-run real report capture smoke with Operator Gate, export/capture and parser enabled. |

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

## MVP-014D Recommended Scope

Title: MVP-014D - One-run Real Report Capture Smoke

Objective: Run one gated real smoke with report export/capture enabled and parse
enabled. MVP-014D must not run multi-run execution, a tournament, optimization
or 10/50/100 public backtests.
