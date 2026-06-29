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
10. Fix Strategy Tester report export/capture. [recommended next]
11. Add installer and portable package after release review. [future]

## Current Stage

PROJECT_STAGE = advanced_technical_mvp_not_final_product

REAL_MT5_STATUS = one_run_smoke_completed_no_report_captured

NEXT_REQUIRED_STEP = report_export_capture_fix_before_multi_run

## Recent MVP Status

| MVP | Status | Notes |
| --- | --- | --- |
| MVP-013C | completed_or_in_pr | First gated one-run real MT5 smoke executed. |
| MVP-013D | completed_or_reviewed | Real smoke result reviewed and documented. |
| MVP-014A | completed | Capture contract and conservative parser merged. |
| MVP-014B | in_pr_no_report_found | One real capture smoke ran, but no official Strategy Tester report was found. |
| MVP-014C | recommended_next | Define/fix Strategy Tester report export before any multi-run smoke. |

## MVP-014C Recommended Scope

Title: MVP-014C - MT5 Strategy Tester Report Export Configuration

Objective: Fix or define how MT5 Strategy Tester should export official reports
so that the next one-run real smoke can capture a parseable report.

MVP-014C must not start a tournament, must not run 100 backtests and must remain
behind explicit Operator Gate controls for any real smoke retry.
