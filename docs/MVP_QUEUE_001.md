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

Use:

```powershell
python factory\mvp_factory.py --list
python factory\mvp_factory.py --next
python factory\mvp_factory.py --generate-prompt MVP-010
```

The initial 10-MVP queue was completed after `MVP-010 Online Leaderboard Spec`.
MVP-011 extends the queue with licensing, brand, contribution, submission and
official ranking governance.

Recommended next step: `MVP-012 Real MT5 Smoke Operator Gate`.
