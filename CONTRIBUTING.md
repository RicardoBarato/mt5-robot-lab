# Contributing

Thank you for helping improve MT5 Robot Lab.

This repository is public and must remain safe for open collaboration. Do not
submit private trading reports, credentials, broker account details or local
machine paths.

## Workflow

1. Open an issue or draft a small pull request.
2. Use a focused branch.
3. Keep each PR narrow and reviewable.
4. Include tests or update existing tests when behavior changes.
5. Run the local validation commands before requesting review.

Recommended validation:

```powershell
python -m compileall app tests tools factory
python -m unittest discover -s tests
python app\mt5_robot_lab_app.py --self-test
python tools\publication_guard.py .
git diff --check
```

## Public Safety Rules

Do not submit:

- credentials;
- `.env` files;
- real `.set` files;
- `.ex5` files;
- private reports;
- private broker logs;
- account numbers;
- broker names or servers from a private account;
- local paths;
- raw MT5 Strategy Tester output with private details.

## Project Boundaries

Pull requests in this repository must not touch:

- PayoffGrid;
- ONPN11 or financial-panel-br;
- `ea-xau`;
- unrelated private projects.

Cross-project integration should be documented first and implemented only after
an explicit scoped mission.

## Leaderboard Contributions

Until official upload terms exist, leaderboard contributions must use sample or
synthetic data.

Do not submit real leaderboard packages for public ranking yet. Future
submissions must use the official validation model and must not include private
data.

## Results Policy

Positive and negative results are both useful. Backtests are research artifacts,
not promises of profit and not financial recommendations.

Risk flags such as grid, martingale, no-stop behavior, high drawdown and high
exposure should be disclosed rather than hidden.
