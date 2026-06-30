# Terminal DataDir EX5 Contract

MVP-014K defines the terminal-side contract that must pass before another real
MT5 smoke retry is allowed.

## Problem

The blocker is not Operator Gate wording and it is not the runtime marker
handoff fixed by MVP-014H. MVP-014I reached the Strategy Tester launch path, but
the EA did not execute and no official report was captured. MVP-014J diagnosed
the current likely root cause as:

```text
compiled_ex5_marker_not_verified_in_terminal_datadir
```

That means the project can see a local readiness marker, but it has not proven
that the compiled EA exists in the `MQL5/Experts` folder of the terminal DataDir
used by Strategy Tester.

## Required Proof

Before a new real retry, the system must prove all of these without launching
MT5:

- terminal DataDir is known and consistent;
- compiled EX5 exists under the terminal DataDir;
- the Strategy Tester `Expert` value maps to that compiled EX5;
- the expert path is relative, not absolute;
- the expert path does not include `.mq5` or `.ex5`;
- optional ExpertParameters, if required, live under the terminal DataDir;
- the report path remains private;
- `Optimization=0`;
- `ReplaceReport=1`;
- `ShutdownTerminal=1`;
- close-after-run policy remains ready.

## Command

```powershell
python app\mt5_robot_lab_app.py --terminal-contract-audit
```

This command writes sanitized public summaries and does not launch MT5,
MetaEditor, Strategy Tester, compile an EX5 or execute an EA.

## Current Decision

The current MVP-014K audit is blocked:

```text
terminal_contract_audit=FAIL
compiled_ex5_verified_in_terminal_datadir=false
terminal_datadir_consistent=false
expert_mapping_valid_for_tester=false
ready_for_real_retry=false
```

The next real retry remains blocked until this command returns PASS.

## Next MVP

`MVP-014L - One-run Real Retry With Terminal Contract Audit PASS` may be
requested only after:

```text
--real-mt5-preflight PASS
--real-mt5-runtime-dry-run PASS
--terminal-contract-audit PASS
fresh Operator Gate approval
clean worktree
```

Controlled multi-run execution, public ranking, 10/50/100 backtest runs and
optimization remain blocked.
