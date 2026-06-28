# Online Ranking Readiness

MVP-009 prepared the local submission package needed by a future online ranking
system. MVP-010 defines the first public leaderboard specification.

The future leaderboard can use validated packages to compare candidates by:

- asset;
- broker symbol;
- timeframe;
- starting balance;
- test period;
- risk mode;
- maximum drawdown tolerance;
- profit factor;
- net profit;
- total trades.

## Current State

- Local package generation exists.
- Local package validation exists.
- Local hashes exist.
- Local leaderboard schema exists.
- Public-safe leaderboard samples exist.
- Ranking categories are documented.
- No online upload exists.
- No public leaderboard exists.
- No service or API is called.
- No account, broker server or private runtime data is stored.

## Future Requirements

Before online submission is enabled, the project should implement:

- accepted package versions;
- server-side validation rules;
- duplicate detection;
- anti-tamper checks;
- abuse prevention;
- disclosure rules for backtests and smoke samples.
- user identity or display-name policy;
- replay or witness validation for high-ranking entries.

## MVP-010 Documents

- `docs/ONLINE_LEADERBOARD_SPEC.md`
- `docs/LEADERBOARD_CATEGORIES.md`
- `docs/SUBMISSION_VALIDATION_MODEL.md`
- `docs/COMMUNITY_AND_MONETIZATION_MODEL.md`
- `docs/LICENSING_AND_BRAND_BOUNDARY.md`

## Open software, official ranking

MT5 Robot Lab is open software for local MT5 strategy tournament research. The
official online ranking and verified badges are separate project-controlled
services planned for the future.

MVP-011 adds the policy boundary for licensing direction, brand usage,
contribution rules, submission terms draft and official ranking governance.

## Disclosure

Backtests and smoke samples are research artifacts. They are not promises of
profit and must not be presented as financial recommendations.
