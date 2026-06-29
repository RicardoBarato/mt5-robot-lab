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
| Hardening | MT5 Close After Real Run Policy | high | in_progress |
| MVP-014C | MT5 Strategy Tester Report Export Configuration | high | recommended_next |

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

The next recommended step is `MVP-014C MT5 Strategy Tester Report Export
Configuration`.

Before MVP-014C, every real execution path must carry the close-after-run
policy:

```text
mt5_close_policy=always_after_real_run
```

Após a execução real, o MT5 será fechado para manter o ambiente limpo e evitar processos presos.

MVP-014C objective:

```text
Fix or define how MT5 Strategy Tester should export official reports so that
the next one-run real smoke can capture a parseable report.
```
