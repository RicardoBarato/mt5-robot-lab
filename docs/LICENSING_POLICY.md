# Licensing Policy

This document is a project policy proposal. It is not legal advice and it is not
final legal advice. In short: not final legal advice. A qualified attorney should
review the final licensing model before any commercial service, hosted ranking
or paid feature is launched.

## Software Core

MT5 Robot Lab is intended to remain open software for local MetaTrader 5
strategy tournament research.

Recommended licensing direction for the software core:

- GPL-3.0-only or AGPL-3.0-only as a proposal;
- keep the repository open and auditable;
- do not restrict commercial use if the project presents itself as open-source;
- do not try to prohibit resale of the software inside an open-source license;
- preserve GPL obligations when importing or deriving from GPL code;
- document license compatibility before adding third-party code.

This repository does not change its final license in MVP-011. The license
direction above is a proposal for future review.

## Official Service

The official online ranking can have separate terms from the local software.

Policy direction:

- ranking submission is optional;
- local software use does not require upload;
- local research does not require an account;
- official verified status depends on a validated package;
- official verified status can be revoked if validation fails later;
- the official ranking can define category, abuse and display rules.

The official service boundary must not convert local open software into a
closed mandatory service.

## Generated Robots and Candidates

MT5 Robot Lab can generate or mutate robot candidates. These artifacts need a
clear ownership and license trail.

Policy direction:

- distinguish generated code, source seeds, derived candidates and results;
- candidates derived from GPL seeds should preserve GPL obligations;
- candidates using third-party code must preserve upstream notices;
- local result files and submission packages can have future publication terms;
- publication terms should govern display rights, not ownership of unrelated
  private code;
- users should only submit candidates they have the right to publish.

## Results and Submission Packages

Results are research artifacts and may be benchmarked by future services.

Submission package policy direction:

- future upload is optional;
- result publication terms should be explicit;
- public summaries can be displayed in official rankings;
- private reports, credentials, `.set` files and `.ex5` files must not be
  submitted;
- public results are benchmark/backtest artifacts, not trading signals.

## Current MVP-011 Decision

MVP-011 does not finalize legal terms and does not change the repository license.
It records a policy direction for future review.
