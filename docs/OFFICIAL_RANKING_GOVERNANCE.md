# Official Ranking Governance

The official ranking is a future project-controlled service. It is separate from
local software usage.

## Core Principles

- The official ranking is controlled by the project.
- The local software remains independent.
- Submission is optional.
- Official verified status depends on validation.
- Official categories can change as the product matures.
- Results can be removed if they violate policy.
- The leaderboard is not a guarantee of real-world performance.

## Result Classes

Future rankings should separate:

- `sample`: generated example data, not a real run;
- `smoke`: limited test path or one-candidate diagnostic;
- `real_backtest`: local Strategy Tester result submitted by a user;
- `official_verified`: package accepted by future official validation.

These classes should never be mixed without visible labels.

## Category Governance

Official categories may include:

- asset;
- broker symbol;
- timeframe;
- initial balance;
- test period;
- risk mode;
- maximum drawdown tolerance;
- ranking mode.

The project may add, rename or retire categories if needed to reduce confusion
or abuse.

## Removal and Correction

The project may remove or correct entries that:

- contain private data;
- use misleading names;
- fail validation;
- contain inconsistent hashes;
- misrepresent sample data as a real backtest;
- misrepresent a backtest as live performance;
- violate contribution or submission policies.

## Local Independence

Users may run the local software without joining the official ranking. Local
usage does not imply endorsement, validation or upload.
