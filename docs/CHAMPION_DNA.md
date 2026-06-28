# Champion DNA v2

Champion DNA v2 is the public-safe research record for a ranked robot
candidate. It explains why a candidate became a champion and preserves the
parameters, metrics, risk profile and hashes needed for future review.

It is not a live trading approval and it does not imply future performance.

## Required Fields

Champion DNA v2 supports:

```text
champion_id
candidate_id
rank
lab_id
lab_name
source_seed_id
source_seed_file
source_mq5_hash
candidate_file
candidate_hash
requested_symbol
broker_symbol
timeframe
timeframe_minutes
backtest_years
initial_balance_usd
final_balance_usd
net_profit_usd
max_drawdown_usd
max_drawdown_pct
profit_factor
expected_payoff
total_trades
win_rate
largest_loss_streak
risk_profile
risk_mode
max_drawdown_tolerated_pct
ranking_profile
ranking_reason
martingale_used
grid_used
no_stop_used
risk_flags
intelligence_mode
codex_used
codex_authorized
mutation_mode
parameter_changes
code_changes_summary
generated_from_candidate_id
generation_number
created_at
test_run_id
report_path
notes
```

## Parameter Diff

Parameter changes are stored as a list:

```text
parameter
before
after
change_type
risk_impact
```

Allowed `risk_impact` values:

```text
neutral
risk_increase
risk_decrease
profit_aggressive
unknown
```

## Risk Profile Integration

Champion DNA records whether the champion was selected under:

- `wild`: Wild Mode, 100% drawdown tolerance for research ranking.
- `controlled_risk`: Controlled Risk Mode, 20% drawdown tolerance and stricter
  treatment of grid, martingale and no-stop flags.

The record includes `ranking_reason`, `risk_flags`, `martingale_used`,
`grid_used` and `no_stop_used`.

## Public Outputs

MVP-008 writes safe sample outputs:

```text
reports/public/sample_champion_dna_v2.json
reports/public/sample_champion_dna_v2.md
```

Future champion folders should use:

```text
champions/<champion_id>/
  champion_dna.json
  parameter_diff.md
  metrics.json
  source_hashes.json
  public_summary.md
```

## Boundaries

Champion DNA v2 must not include passwords, tokens, account identifiers, broker
server details, private local paths, real logs, `.set` files or `.ex5` files.
