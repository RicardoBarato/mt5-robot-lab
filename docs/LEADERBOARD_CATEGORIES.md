# Leaderboard Categories

MT5 Robot Lab should rank robot submissions in separate categories, similar to
hardware benchmark leaderboards.

## Asset and Symbol

Primary asset categories:

```text
XAUUSD
USTEC
US30
EURUSD
GBPUSD
BTCUSD
manual_broker_symbol
```

`requested_symbol` is what the user selected. `broker_symbol` is the real symbol
name used by the local MetaTrader 5 installation.

Examples:

```text
requested_symbol=XAUUSD, broker_symbol=XAUUSDm
requested_symbol=USTEC, broker_symbol=USTEC.cash
requested_symbol=BTCUSD, broker_symbol=BTCUSD.
```

## Timeframes

Supported timeframes:

```text
M1
M5
M15
M30
H1
H4
D1
```

## Backtest Window

Supported period categories:

```text
6_months
1_year
2_years
5_years
custom
```

`custom` should require an explicit start and end date in future versions.

## Initial Balance

Supported balance categories:

```text
1000
10000
50000
custom
```

The default educational balance remains USD 10,000.

## Risk Profiles

Risk categories:

```text
Wild Mode
Controlled Risk Mode
max DD 10%
max DD 20%
max DD 30%
max DD 50%
max DD 100%
```

Wild Mode permits aggressive strategies such as grid, martingale, pyramiding,
high exposure and no-stop candidates. The leaderboard must disclose these risk
flags instead of hiding them.

Controlled Risk Mode should prioritize candidates that stay inside the selected
drawdown tolerance.

## Ranking Modes

Supported ranking modes:

```text
highest_net_profit
highest_profit_factor
lowest_drawdown
profit_per_drawdown
most_stable
```

Each public view should show the selected ranking mode and the category key.

## Category Key

The schema uses a stable category key:

```text
asset|timeframe|years|initial_balance|risk_mode|max_drawdown_tolerance
```

Example:

```text
XAUUSD|M5|2.0y|10000|wild|dd100.0
```
