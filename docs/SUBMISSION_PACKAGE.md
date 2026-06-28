# Submission Package v1

Submission Package v1 is the local, public-safe package format for future MT5
Robot Lab online ranking submissions.

It does not upload anything. It does not call external APIs. It is not a
leaderboard implementation.

## Package Structure

Sample package:

```text
reports/public/submission_package_sample/
  submission_manifest.json
  champion_dna.json
  tournament_summary.json
  risk_profile.json
  config_public_summary.json
  file_hashes.json
  validation_report.json
  public_summary.md
```

No `.zip` is created in MVP-009.

## Manifest

`submission_manifest.json` stores:

```text
submission_id
created_at
product_name
app_version
package_version
lab_id
lab_name
requested_symbol
broker_symbol
timeframe
timeframe_minutes
backtest_years
initial_balance_usd
risk_profile
risk_mode
max_drawdown_tolerated_pct
ranking_profile
champion_id
candidate_id
net_profit_usd
max_drawdown_pct
profit_factor
total_trades
win_rate
mt5_real_run
backtest_real_run
tournament_100_run
codex_used
codex_authorized
local_only
upload_ready
validation_status
file_hashes
notes
```

Sample packages must keep:

```text
mt5_real_run=false
backtest_real_run=false
tournament_100_run=false
local_only=true
upload_ready=false
validation_status=sample_not_real_backtest
```

## Validation

Validation checks:

- required files exist;
- JSON files parse;
- manifest required fields exist;
- file hashes match;
- no forbidden file patterns are present;
- no common sensitive strings are present;
- no private package roots are included.

## Boundary

The package is designed for future ranking readiness. It is not proof of live
performance, not a recommendation and not an upload to any service.
