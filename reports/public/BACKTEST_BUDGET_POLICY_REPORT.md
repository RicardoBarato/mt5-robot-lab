# Backtest Budget Policy Report

Status: product_contract_added

## Official Product Values

- minimum_public_backtests: 10
- default_backtests: 10
- recommended_options: 10, 50, 100
- custom_backtests_allowed: true
- custom_backtests_minimum: 10
- ranking_mode: single_unified_ranking
- sequential_only: true
- max_concurrent_mt5: 1
- close_mt5_after_each_backtest: true
- checkpoint_after_each_backtest: true
- pause_stop_supported: true
- internal_smoke_minimum: 1

## Transparency Fields

Every public/ranking result must disclose:

- backtests_requested
- backtests_completed
- search_budget
- generation_id
- candidate_id

## Dev-Only One-Run Mode

One backtest remains permitted only for internal smoke/dev work and must be
marked:

- not_for_ranking
- not_for_product_claim
- dev_only

## Safety Boundary

- MT5 real run: false
- Backtest real run: false
- Strategy Tester run: false
- EA executed: false
- Tournament 100 run: false
- Credentials stored: false
- Private files committed: false

## Next Step

MVP-014C Strategy Tester Report Export Configuration.
