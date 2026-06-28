# Tournament Config Wizard

MVP-002 adds the safe tournament configuration model used by the desktop wizard.
It does not run MT5, Strategy Tester, real backtests or a 100-run tournament.

## Fields

- `lab_id`
- `lab_name`
- `lab_path`
- `requested_symbol`
- `broker_symbol`
- `timeframe`
- `timeframe_minutes`
- `backtest_years`
- `initial_balance_usd`
- `max_backtests`
- `champion_count`
- `intelligence_mode`
- `output_formats`
- `mt5_terminal_path`
- `mt5_metaeditor_path`
- `codex_enabled`
- `codex_authorized`
- `created_at`
- `updated_at`

## Official Defaults

- Lab: `ea-xau` / `XAU Robot Lab`
- Requested symbol: `XAUUSD`
- Timeframe: `M5`
- Backtest years: `2`
- Initial balance: `10000`
- Max backtests: `100`
- Champion count: `10`
- Intelligence mode: `local_auto`
- Output formats: `csv`, `md`, `xlsx`

## Validation Rules

- Numeric fields must be positive.
- `champion_count` must be less than or equal to `max_backtests`.
- `requested_symbol` must not be empty.
- `timeframe` must be one of `M1`, `M5`, `M15`, `M30`, `H1`, `H4`, `D1`.
- `intelligence_mode` must be `local_auto`, `codex_assisted` or `seeds_only`.
- `output_formats` must be `csv`, `md` or `xlsx`.

## Local Config Boundary

Real local tournament configuration belongs in `config/local.tournament.json`,
which is ignored by Git. Public examples and previews must not include
passwords, tokens, account details, broker servers or sensitive local MT5 paths.

## Dry-Run Packet

`Prepare Dry-Run Packet` writes public-safe preview files:

- `reports/public/tournament_config_preview.md`
- `reports/public/tournament_config_preview.json`

These files describe the selected tournament settings without running MT5.
