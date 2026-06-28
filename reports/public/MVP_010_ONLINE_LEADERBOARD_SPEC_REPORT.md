# MVP-010 Online Leaderboard Spec Report

## Objective

Define the future public leaderboard model for MT5 Robot Lab without deploying
or creating an online service.

## Files Changed

- `app/core/leaderboard_schema.py`
- `app/mt5_robot_lab_app.py`
- `tests/test_leaderboard_schema.py`
- `docs/ONLINE_LEADERBOARD_SPEC.md`
- `docs/LEADERBOARD_CATEGORIES.md`
- `docs/SUBMISSION_VALIDATION_MODEL.md`
- `docs/COMMUNITY_AND_MONETIZATION_MODEL.md`
- `docs/LICENSING_AND_BRAND_BOUNDARY.md`
- `docs/ONLINE_RANKING_READINESS.md`
- `docs/MVP_QUEUE_001.md`
- `README.md`
- `factory/mvp_queue.json`
- `factory/mvp_status.json`

## Schema

MVP-010 adds a local leaderboard schema with entry fields, category generation,
entry validation and ranking helpers.

## Sample Outputs

Expected public-safe samples:

- `reports/public/leaderboard_sample.json`
- `reports/public/leaderboard_sample.md`

The samples are explicitly marked as non-real:

```text
mt5_real_run=false
backtest_real_run=false
upload_ready=false
leaderboard_created=false
online_upload=false
```

## Limits

- No online upload was performed.
- No leaderboard service was created.
- No backend, site, account system, AdSense, payment system, `.zip`, `.exe`,
  release or tag was created.
- Sample values are not real backtest evidence.

## Scope Confirmations

- MT5 real did not run.
- Strategy Tester did not run.
- 100-test tournament did not run.
- `ea-xau` was not touched.
- PayoffGrid was not touched.
- ONPN11 was not touched.
- No private files were copied.

## Next MVP

Recommended next MVP: `MVP-011 Licensing and Contribution Policy`.
