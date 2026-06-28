# MVP-013 Real MT5 Smoke Prep

MVP-013 prepares the operator workflow for a future real MT5 smoke execution.
This document is preparation only. It does not run MetaTrader 5, does not run a
backtest, and does not create a release package.

MVP-013 Real MT5 Smoke Execution só pode ocorrer depois deste checklist.

Official credential boundary:

O MT5 Robot Lab não armazena senha, conta, servidor ou credenciais. O usuário deve fazer login diretamente no MetaTrader 5.

## Scope

MVP-013 prep defines:

- the manual installation and login checklist;
- the requirement that the operator opens MT5 manually;
- the requirement that any account login happens inside MT5;
- the requirement that the desired symbol is visible in Market Watch;
- the requirement that symbol history and timeframe data are available;
- the Operator Gate requirement before any real smoke execution.

## Operator Gate

The Operator Gate remains mandatory. A future real MT5 smoke can only proceed
after explicit operator approval and must remain limited to one controlled
execution. The gate must continue to block:

- accidental real MT5 execution;
- credential collection;
- strategy optimization;
- tournament loops;
- 100-backtest runs.

## Future Smoke Boundary

The future MVP-013 execution mission may run at most one real smoke execution
after manual approval. It must not become a tournament, optimizer, release
build, live-trading tool, or performance claim.

## Completion Criteria

This prep is complete when:

- `docs/MT5_MANUAL_PREP_CHECKLIST.md` exists;
- the public report exists;
- the Operator Gate is referenced;
- validations pass;
- no MT5 real run occurred;
- no credentials were requested or stored.
