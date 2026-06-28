# Online Leaderboard Spec

MVP-010 defines the future public leaderboard model for MT5 Robot Lab.

This is a specification only. It does not create a website, backend, upload
endpoint, account system, payment system, advertising integration or public
ranking service.

## Goal

The future leaderboard should compare local tournament submissions in a way that
is reproducible, category-aware and clear about risk.

The leaderboard should accept only validated submission packages produced by the
local app. A package must contain public-safe metadata, Champion DNA, risk
profile data, hashes and a validation report.

## Current MVP-010 Boundary

MVP-010 provides:

- leaderboard categories;
- leaderboard entry schema;
- ranking modes;
- submission validation model;
- community and monetization model;
- licensing and brand boundary;
- public-safe sample output.

MVP-010 does not provide:

- online upload;
- live leaderboard;
- user accounts;
- server-side validation;
- payments;
- AdSense or ads code;
- real MT5 execution;
- real backtest execution.

## Entry Lifecycle

Future leaderboard entry lifecycle:

1. User runs a local tournament.
2. MT5 Robot Lab creates Champion DNA.
3. MT5 Robot Lab creates a Submission Package.
4. The package is locally validated.
5. The user chooses whether to submit it to a future public service.
6. A future server validates the package again.
7. If accepted, the entry is ranked in matching categories.

No package should be accepted by a future public service until server-side
validation exists.

## Required Entry Fields

The public entry schema includes:

```text
entry_id
submission_id
champion_id
user_display_name
team_name
country
product_version
package_version
asset
requested_symbol
broker_symbol
timeframe
timeframe_minutes
backtest_years
initial_balance_usd
risk_profile
risk_mode
max_drawdown_tolerated_pct
ranking_mode
net_profit_usd
final_balance_usd
max_drawdown_pct
profit_factor
total_trades
win_rate
martingale_used
grid_used
no_stop_used
mt5_real_run
backtest_real_run
validation_status
upload_ready
created_at
public_summary_path
```

## Ranking Modes

Supported ranking modes for the future service:

- `highest_net_profit`
- `highest_profit_factor`
- `lowest_drawdown`
- `profit_per_drawdown`
- `most_stable`

The default benchmark-style ranking is `highest_net_profit`, but the UI should
make risk filters visible.

## Disclosure Rules

Every future leaderboard page should state:

- results are backtest or research artifacts;
- results are not financial recommendations;
- local broker symbol names can vary;
- risk modes must be displayed near returns;
- drawdown and total trades must be visible;
- real account claims are outside this repository.

## Public Safety Rules

Leaderboard entries must not contain:

- passwords;
- API keys;
- local paths;
- account numbers;
- broker login details;
- broker server details;
- private reports;
- raw MT5 logs;
- `.set` files;
- `.ex5` files.

## MVP-010 Result

The MVP-010 implementation creates a local schema and sample files only:

```text
reports/public/leaderboard_sample.json
reports/public/leaderboard_sample.md
```

Both samples explicitly keep:

```text
mt5_real_run=false
backtest_real_run=false
upload_ready=false
leaderboard_created=false
online_upload=false
```
