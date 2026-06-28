# MT5 Robot Lab

Local Strategy Tournament for MetaTrader 5.

`MT5 Robot Lab` is a Windows desktop app for configuring, running and ranking
local MetaTrader 5 robot tournaments across symbols, timeframes, test windows,
balance sizes and intelligence modes.

This repository is a bootstrap scaffold. It does not run real MT5 yet, does not
perform live trading and does not promise profit.

## Product Vision

The product should let a user:

1. Open a desktop app without using CLI.
2. Select a connected robot laboratory such as `ea-xau`.
3. Detect a local MetaTrader 5 installation.
4. Choose asset, broker symbol and timeframe.
5. Choose an intelligence mode.
6. Configure tournament size and balance.
7. Run controlled local research workflows.
8. Review Champion DNA.
9. Export spreadsheet and Markdown reports.

## Relationship With ea-xau

`ea-xau` remains the XAUUSD robot laboratory and ranking archive. `MT5 Robot Lab`
is the future desktop software that can connect to `ea-xau` and later to other
laboratories such as `ea-ustec`, `ea-us30` or `ea-btc`.

This project does not edit `ea-xau` directly.

## Public Repository Governance

`main` is intended to stay protected. Changes should use branch + PR workflow,
with CI required before merge. Public artifacts must not include private reports,
credentials, broker/account details, local paths, `.set` files, `.ex5` files or
real MT5 logs.

CI and public checks must not run real MT5, real Strategy Tester backtests or
live trading. PayoffGrid and ONPN11 / financial-panel-br are outside the scope
of this project.

## Intelligence Modes

- `local_auto`: local programmed mutation without external AI.
- `codex_assisted`: optional Codex mission-packet workflow with explicit user
  authorization.
- `seeds_only`: run included base robots only.

Codex is not required and must not be installed, logged in or executed silently.

## Desktop UI Foundation

The first desktop UI pass uses a dark premium Windows-style layout with status
cards, an MT5 detection action, tournament configuration placeholders,
intelligence mode selection and a Champion DNA preview area. The user-facing
goal is to avoid manual CLI usage for normal workflows while keeping real MT5
execution disabled until the adapter is explicitly implemented.

MVP-001 adds Desktop Navigation v2 with 11 in-app screens: Welcome, Lab
Selection, MT5 Setup, Symbol and Timeframe, Intelligence Mode, Tournament Setup,
Running Backtests, Champions Ranking, Champion DNA, Export Spreadsheet and
Settings. The same screen registry is validated in headless self-tests.

## Grand MVP Factory

MT5 Robot Lab uses a Grand MVP Factory workflow to evolve the desktop app
through large, controlled, validated MVP batches.

```powershell
python factory\mvp_factory.py --self-test
python factory\mvp_factory.py --list
python factory\mvp_factory.py --next
python factory\mvp_factory.py --generate-prompt MVP-001
```

## Champion DNA

Champion DNA v2 records the source seed, candidate hash, source hash,
parameters, parameter diffs, metrics, risk profile, drawdown tolerance, risk
flags and public summary behind each ranked robot candidate. It is a research
ledger, not a live trading approval.

Current public-safe sample outputs:

```text
reports/public/sample_champion_dna_v2.json
reports/public/sample_champion_dna_v2.md
```

Champion DNA v2 integrates with the smoke tournament engine and risk profile
ranking. Smoke/dry-run records explicitly keep `mt5_real_run=false` and
`backtest_real_run=false`.

## Exports

The scaffold can generate sample CSV and Markdown summaries. If `openpyxl` is
available, it can also write a sample XLSX file. Missing `openpyxl` is not a
failure.

## Submission Package

Submission Package v1 creates a local public-safe folder for future online
ranking workflows. It includes Champion DNA, tournament summary, risk profile,
public configuration, hashes, a manifest and a validation report.

Current sample:

```text
reports/public/submission_package_sample/
```

The package is local only. It is not uploaded, it is not a leaderboard entry and
it is not a real backtest claim.

## Online Leaderboard Spec

MVP-010 defines the future leaderboard model for benchmark-style rankings by
asset, broker symbol, timeframe, test window, starting balance, risk mode and
drawdown tolerance.

Current public-safe sample outputs:

```text
reports/public/leaderboard_sample.json
reports/public/leaderboard_sample.md
```

The leaderboard is a specification only. This repository does not create an
online service, does not upload submissions, does not implement payments or ads
and does not claim real trading performance.

## MT5 Boundary

MetaTrader 5 must be installed separately by the user. This app must not bundle
MT5, broker installers, credentials, account details, raw reports or private
logs.

## Development Validation

```powershell
python -m compileall app tests tools
python -m unittest discover -s tests
python app\mt5_robot_lab_app.py --self-test
python tools\publication_guard.py .
```

## Status

Bootstrap only. No real MT5 run, no real backtest, no installer, no portable zip
and no financial recommendation.
