# MT5 Robot Lab

Local Strategy Tournament for MetaTrader 5.

`MT5 Robot Lab` is a Windows desktop app for configuring, running and ranking
local MetaTrader 5 robot tournaments across symbols, timeframes, test windows,
balance sizes and intelligence modes.

This repository is an advanced technical MVP and MVP factory. A gated one-run
real MT5 smoke has been executed under Operator Gate controls. The project has
not yet captured a parseable official Strategy Tester report and has not run
multi-run tournaments or 100-backtest optimization. It does not perform live
trading and does not promise profit.

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
execution behind Operator Gate controls and limited smoke boundaries.

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

## Open software, official ranking

MT5 Robot Lab is open software for local MT5 strategy tournament research. The
official online ranking and verified badges are separate project-controlled
services planned for the future.

Policy documents:

- `docs/LICENSING_POLICY.md`
- `docs/BRAND_AND_TRADEMARK_POLICY.md`
- `CONTRIBUTING.md`
- `CODE_OF_CONDUCT.md`
- `docs/SUBMISSION_TERMS_DRAFT.md`
- `docs/OFFICIAL_RANKING_GOVERNANCE.md`

MVP-011 does not change the repository license and does not finalize legal
terms.

## MT5 Boundary

MetaTrader 5 must be installed separately by the user. This app must not bundle
MT5, broker installers, credentials, account details, raw reports or private
logs.

## Real MT5 Smoke Operator Gate

MVP-012 adds an explicit operator approval gate for future one-run real MT5 smoke
execution. By default, runners remain blocked and safe.

Safe preview commands:

```powershell
python app\mt5_robot_lab_app.py --operator-gate-self-test
python app\mt5_robot_lab_app.py --preview-real-mt5-smoke-gate
```

The preview does not launch MT5, does not run Strategy Tester and does not run a
real backtest.

## Pre-Real MT5 Safety Hardening

MVP-013A keeps real MT5 execution blocked while hardening the boundary around
public artifacts, self-test outputs, executable path validation, path redaction,
submission package scanning and CI coverage.

Self-tests write temporary runtime artifacts under ignored `runs/self_tests/`
paths. They must not modify tracked `reports/public` files.

## Real MT5 Smoke State

MVP-013C executed the first gated one-run local MT5 smoke. MVP-014B then
integrated the capture/parser contract and recorded the current state:

- execution-level smoke worked under the explicit Operator Gate;
- raw local artifacts remain private and ignored by Git;
- the public summary is sanitized;
- no credentials, account details or broker server details are stored;
- the official Strategy Tester report was not captured;
- no parseable real result exists yet;
- the close-after-real-run policy is now mandatory for every future real run;
- 100-backtest tournaments remain blocked.

MVP-014D attempted one report-capture smoke and failed without retry. The
sanitized diagnosis is:

```text
exit_code=3294954941
failure_stage=strategy_tester_failed_before_ea
report_file_found=false
parse_status=no_report_found
```

MVP-014E adds the required preflight layer before any retry. A future retry must
prove the expected expert path, compiled EX5, private report contract,
`ReplaceReport=1`, `ShutdownTerminal=1`, one-run smoke scope and close-after-run
policy before launching MT5 again.

MVP-014F adds the safe preflight readiness command:

```powershell
python app\mt5_robot_lab_app.py --real-mt5-preflight
```

The command writes sanitized public summaries, does not launch MT5, does not
start Strategy Tester and does not execute an EA. It records
`ready_for_retry=true` only for the contract-readiness path; the next real run
still requires explicit Operator Gate approval.

## MT5 Close After Real Run

Every future gated real smoke or real backtest must use:

```text
mt5_close_policy=always_after_real_run
```

Após a execução real, o MT5 será fechado para manter o ambiente limpo e evitar processos presos.

The app may close only the MT5 process it starts and controls. If MT5 was
already open outside the app, the run must record `manual_close_required=true`
instead of terminating that external session.

## Backtest Budget Product Policy

Public and ranking runs use one unified ranking with transparent search budget
disclosure:

```text
minimum_public_backtests=10
default_backtests=10
recommended_options=10,50,100
custom_backtests_allowed=true
custom_backtests_minimum=10
ranking_mode=single_unified_ranking
```

Every public/ranking result must show `backtests_requested`,
`backtests_completed`, `search_budget`, `generation_id` and `candidate_id`.
One-run execution is internal smoke/dev only and must be marked
`not_for_ranking`, `not_for_product_claim` and `dev_only`.

Execution must remain sequential:

```text
sequential_only=true
max_concurrent_mt5=1
close_mt5_after_each_backtest=true
checkpoint_after_each_backtest=true
pause_stop_supported=true
```

The system must never open 10, 50 or 100 MT5 terminals at the same time.

## Strategy Tester Report Export Contract

MVP-014C prepares the report export/capture contract for the next one-run real
smoke. It does not run MT5, does not run Strategy Tester and does not execute an
EA.

Future tester configuration must include:

```text
[Tester]
Report=<private_report_base>
ReplaceReport=1
ShutdownTerminal=1
```

Raw Strategy Tester reports must stay under `reports/private/real_mt5_smoke/`.
Public summaries must stay sanitized. Controlled multi-run execution remains
blocked until a future one-run smoke captures and parses an official report.

The next required technical step is `MVP-014G - One-run Real Retry After
Preflight`, still limited to one Operator Gate execution and still blocked from
multi-run or 10/50/100 public backtests.

## Development Validation

```powershell
python -m compileall app tests tools factory
python -m unittest discover -s tests
python app\mt5_robot_lab_app.py --self-test
python app\mt5_robot_lab_app.py --operator-gate-self-test
python app\mt5_robot_lab_app.py --preview-real-mt5-smoke-gate
python tools\publication_guard.py .
python factory\mvp_factory.py --self-test
git diff --check
git status --short
```

## Status

Advanced technical MVP, not a final product. The project has a desktop
foundation, MVP factory, Operator Gate, publication guard, public/private
artifact boundary and one gated real MT5 smoke attempt. Official report capture
is still unresolved, no parseable real Strategy Tester report has been captured,
real retry is blocked until preflight passes, no multi-run tournament has been
run, no 100-backtest optimization has been run, no installer or portable zip
exists and nothing is a financial recommendation.
