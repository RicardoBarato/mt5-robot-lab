# MVP-008 Champion DNA v2 Report

## Objective

Implement Champion DNA v2 as the public-safe research record for ranked robot
candidates.

## Files Changed

- `app/core/champion_dna.py`
- `app/core/risk_profile_ranking.py`
- `app/core/tournament_engine.py`
- `app/core/export_reports.py`
- `app/mt5_robot_lab_app.py`
- `tests/test_champion_dna_v2.py`
- `docs/CHAMPION_DNA.md`
- `docs/MVP_QUEUE_001.md`
- `README.md`
- `factory/mvp_queue.json`
- `factory/mvp_status.json`

## New DNA Fields

Champion DNA v2 adds complete identity, source hash, candidate hash, symbol,
timeframe, metrics, risk profile, risk mode, drawdown tolerance, risk flags,
parameter diffs, adjustment summary and future leaderboard package metadata.

## Risk Profile Integration

The record supports Wild Mode and Controlled Risk Mode. Wild Mode uses 100%
drawdown tolerance for aggressive research ranking. Controlled Risk Mode uses
20% drawdown tolerance and records rejection/downgrade reasons for grid,
martingale or no-stop risk flags.

## Tournament Engine Integration

The smoke tournament engine now writes Champion DNA v2 when a champion is
selected. Smoke records explicitly set:

```text
status=smoke_or_dry_run
mt5_real_run=false
backtest_real_run=false
```

## Outputs Created

- `reports/public/sample_champion_dna_v2.json`
- `reports/public/sample_champion_dna_v2.md`
- `reports/public/MVP_008_CHAMPION_DNA_V2_REPORT.md`

## Tests Run

- `python -m compileall app tests tools factory`
- `python -m unittest discover -s tests`
- `python app\mt5_robot_lab_app.py --self-test`
- `python tools\publication_guard.py .`
- `python factory\mvp_factory.py --self-test`
- `python factory\mvp_factory.py --list`
- `python factory\mvp_factory.py --next`
- `git diff --check`

## Limitations

- No real MT5 execution was performed.
- No real Strategy Tester backtest was performed.
- Smoke metrics remain placeholder values until a later approved real adapter.
- No `.exe`, `.zip`, release or tag was created.

## Scope Confirmations

- MT5 real did not run.
- `ea-xau` was not touched.
- PayoffGrid was not touched.
- ONPN11 was not touched.
- No private files were copied.

## Next MVP

Recommended next MVP: `MVP-009 Submission Package v1`.
