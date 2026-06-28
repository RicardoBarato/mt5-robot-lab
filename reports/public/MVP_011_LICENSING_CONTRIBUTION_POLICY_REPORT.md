# MVP-011 Licensing and Contribution Policy Report

## Objective

Consolidate public policy docs for licensing direction, brand/trademark
boundaries, contribution rules, submission terms draft, official ranking
governance and responsible monetization.

## Documents Created

- `docs/LICENSING_POLICY.md`
- `docs/BRAND_AND_TRADEMARK_POLICY.md`
- `CONTRIBUTING.md`
- `CODE_OF_CONDUCT.md`
- `docs/SUBMISSION_TERMS_DRAFT.md`
- `docs/OFFICIAL_RANKING_GOVERNANCE.md`
- `tests/test_policy_docs.py`

## Licensing Decision

The licensing document records GPL-3.0-only or AGPL-3.0-only as a proposal for
future legal review. MVP-011 does not change the repository license.

The policy states that the project should not prohibit commercial use while
calling itself open-source and should preserve GPL obligations for GPL-derived
code.

## Open Software and Official Ranking

MT5 Robot Lab is open software for local MT5 strategy tournament research. The
official online ranking and verified badges are separate project-controlled
services planned for the future.

Local software use remains independent from any future ranking upload.

## Brand

The brand policy defines MT5 Robot Lab, MT5 Robot Lab Rankings, Official
Verified and Champion DNA Verified as project-controlled public trust signals.

Forks may use code according to license terms, but should not present themselves
as the official ranking if materially changed.

## Contribution

The contribution policy requires focused pull requests, tests, publication
guard validation and strict exclusion of credentials, `.set`, `.ex5`, private
reports, account data, broker server details and unrelated projects.

## Future Submission

The submission terms draft confirms that future uploads are optional, require
validated public-safe packages and can be rejected if invalid, fraudulent,
dangerous, incomplete or misleading.

## Responsible Monetization

The monetization model allows donations, possible future sponsor/donate links,
future ads after policy review and premium analytics, but keeps monetization
separate from risk disclosure and financial recommendations.

## Tests Run

Expected validation set:

```powershell
python -m compileall app tests tools factory
python -m unittest discover -s tests
python app\mt5_robot_lab_app.py --self-test
python tools\publication_guard.py .
python factory\mvp_factory.py --self-test
python factory\mvp_factory.py --list
python factory\mvp_factory.py --next
git diff --check
```

## Limitations

- No final legal terms were created.
- No license file was changed.
- No online ranking, backend, upload, AdSense, `.exe`, `.zip`, release or tag
  was created.
- No real MT5 or real backtest was run.

## Legal Boundary

This MVP is not final legal advice.

## Next MVP

Recommended next MVP: `MVP-012 Real MT5 Smoke Operator Gate`.
