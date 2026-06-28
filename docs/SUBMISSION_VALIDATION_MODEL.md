# Submission Validation Model

The online leaderboard should never trust a client submission directly.

MVP-010 defines the future validation model. It does not implement a backend.

## Validation Levels

### Level 0 - Local Package Validation

Implemented by Submission Package v1.

Checks:

- required files exist;
- JSON files parse;
- manifest fields exist;
- file hashes match;
- private files are absent;
- forbidden artifact patterns are absent.

### Level 1 - Public Entry Schema Validation

Implemented in MVP-010 as local schema helpers.

Checks:

- required leaderboard fields exist;
- timeframe is supported;
- booleans are typed correctly;
- validation status is present;
- common sensitive strings are absent.

### Level 2 - Future Server Validation

Not implemented yet.

Future checks should include:

- submission package version allowlist;
- duplicate package detection;
- hash consistency;
- category consistency;
- suspicious metric ranges;
- abuse throttling;
- user identity validation;
- replay protection.

### Level 3 - Future Replay or Witness Validation

Not implemented yet.

Possible approaches:

- deterministic reproduction bundle;
- signed local run attestation;
- server-side rerun for selected finalists;
- community challenge window.

## Required Disclosures

Every accepted public entry should disclose:

- `mt5_real_run`;
- `backtest_real_run`;
- `initial_balance_usd`;
- `symbol`;
- `broker_symbol`;
- `timeframe`;
- `backtest_years`;
- `net_profit_usd`;
- `max_drawdown_pct`;
- `profit_factor`;
- `total_trades`;
- `risk_mode`;
- risk flags such as martingale, grid and no-stop.

## Rejection Reasons

Future server validation should reject:

- missing required fields;
- invalid JSON;
- hash mismatch;
- unsupported category;
- private file references;
- credentials or tokens;
- local Windows paths;
- raw logs;
- `.set` files;
- `.ex5` files;
- upload attempts marked as samples.

## Current MVP-010 State

Only local sample validation exists. No package is uploaded and no leaderboard is
created.
