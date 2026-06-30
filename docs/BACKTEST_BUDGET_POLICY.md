# Backtest Budget Policy

This document is the official product contract for public backtest counts in
MT5 Robot Lab.

## Official Values

```text
minimum_public_backtests = 10
default_backtests = 10
recommended_options = [10, 50, 100]
custom_backtests_allowed = true
custom_backtests_minimum = 10
ranking_mode = single_unified_ranking
sequential_only = true
max_concurrent_mt5 = 1
close_mt5_after_each_backtest = true
checkpoint_after_each_backtest = true
pause_stop_supported = true
internal_smoke_minimum = 1
```

## Why the Public Minimum Is 10

A single backtest is useful for wiring, smoke checks and parser validation, but
it is too thin for public comparison or ranking. The minimum public budget is 10
so a candidate has at least a small repeated evaluation budget before it can be
presented in a product or ranking context.

## Why 1 Backtest Is Smoke/Dev Only

One-run execution remains allowed internally as:

```text
internal_smoke_minimum = 1
not_for_ranking
not_for_product_claim
dev_only
```

The one-run path verifies that MT5, Strategy Tester, result capture and parser
boundaries work. It must not be used as a public performance claim.

## Recommended Public Options

The primary user-facing options are:

- 10 backtests: default and minimum public run;
- 50 backtests: broader exploration for users with more time;
- 100 backtests: advanced search budget that may take a long time.

Custom counts are allowed only when they are at least 10.

## Unified Ranking

MT5 Robot Lab does not maintain separate rankings for 10, 50 and 100 backtests.
All valid candidates compete in one ranking:

```text
ranking_mode = single_unified_ranking
```

The ranking remains unified because the product should answer one question:
which candidate produced the strongest result under its declared search budget.

## Search Budget Transparency

Every result must disclose:

```text
backtests_requested
backtests_completed
search_budget
generation_id
candidate_id
```

Public reports may also use `backtests_used` as a human-readable synonym for
`backtests_completed`. The exact budget must be visible so a 100-run search is
not confused with a 10-run search.

## Sequential Execution

Every public or ranking run must use:

```text
sequential_only = true
max_concurrent_mt5 = 1
```

The system must never open 10, 50 or 100 MT5 terminals at the same time. Runs
are sequential to reduce process conflicts, stale terminal state, credential
exposure risk, resource spikes and report-capture ambiguity.

## Close and Checkpoint Policy

Every future public/ranking execution must use:

```text
close_mt5_after_each_backtest = true
checkpoint_after_each_backtest = true
pause_stop_supported = true
```

Closing MT5 after each backtest keeps the environment clean and prevents stuck
terminal processes from contaminating later runs. Checkpoints after each
backtest preserve progress if the operator pauses, stops or the machine fails.

## Next Technical Step

The next technical step remains:

```text
MVP-014C Strategy Tester Report Export Configuration
```

MVP-014C must define/fix official Strategy Tester report export before any
public multi-run or ranking execution.

The minimum public budget remains 10 backtests, but MVP-014C does not execute
that budget. MVP-014C only prepares the private report export/capture contract
for the next one-run smoke.
