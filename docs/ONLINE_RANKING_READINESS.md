# Online Ranking Readiness

MVP-009 prepares the local submission package needed by a future online ranking
system.

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
- No online upload exists.
- No public leaderboard exists.
- No service or API is called.
- No account, broker server or private runtime data is stored.

## Future Requirements

Before online submission is enabled, the project should define:

- accepted package versions;
- server-side validation rules;
- duplicate detection;
- anti-tamper checks;
- ranking categories;
- abuse prevention;
- disclosure rules for backtests and smoke samples.

## Disclosure

Backtests and smoke samples are research artifacts. They are not promises of
profit and must not be presented as financial recommendations.
