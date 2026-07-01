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
- the expert path does not include source or compiled file extensions;
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

MVP-014K2 adds a non-executing bootstrap command that resolves the terminal
DataDir and creates the ignored local compiled-EX5 readiness marker only if the
expected EX5 already exists under that terminal DataDir:

```powershell
python app\mt5_robot_lab_app.py --compiled-ex5-readiness-bootstrap
```

MVP-014K3 adds a stricter bootstrap command that can also use exactly one safe
in-repo MQL5 source or an explicitly configured ignored local EX5:

```powershell
python app\mt5_robot_lab_app.py --compiled-ex5-terminal-bootstrap
```

This command never launches `terminal64.exe`, never starts Strategy Tester and
never runs a backtest. It may invoke MetaEditor only for a controlled compile
when a safe source exists and the MetaEditor path is configured.

## Current Decision

The MVP-014K3 bootstrap/audit was blocked:

```text
status=HOLD_MVP_014K3_MQL5_SOURCE_OR_EX5_NOT_FOUND
terminal_data_dir_found=true
datadir_source=appdata_origin_txt
bootstrap_command=HOLD
bootstrap_method=hold_missing_source_or_ex5
metaeditor_real_run=false
mt5_terminal_run=false
compiled_ex5_found_before=false
compiled_ex5_created_or_copied=false
compiled_ex5_found_after=false
compiled_ex5_marker_created=false
terminal_contract_audit=FAIL
compiled_ex5_verified_in_terminal_datadir=false
terminal_datadir_consistent=false
expert_mapping_valid_for_tester=false
ready_for_real_retry=false
blocking_issues=mql5_source_or_ex5_not_found
```

This is an improvement over the previous missing-DataDir state, but it is still
not enough for a real retry. The next real retry remains blocked until a safe
source or ignored local EX5 is provided, the EX5 exists in the resolved terminal
DataDir and the terminal contract audit returns PASS.

## Next MVP

`MVP-014L - One-run Real Retry With Terminal Contract Audit PASS` may be
requested only after:

MVP-014K4 adds a public, non-trading smoke harness source at
`MQL5/Experts/MT5RobotLab/SmokeHarness_Public.mq5` and changes the default
Strategy Tester expert mapping to `MT5RobotLab\SmokeHarness_Public`. The source
has no trade operations, grid, martingale or credential handling. The bootstrap
may invoke MetaEditor only to compile this source into the resolved terminal
DataDir; it still must not launch `terminal64.exe`, Strategy Tester or any
backtest.

```text
--real-mt5-preflight PASS
--real-mt5-runtime-dry-run PASS
--compiled-ex5-terminal-bootstrap PASS
--terminal-contract-audit PASS
fresh Operator Gate approval
clean worktree
```

Controlled multi-run execution, public ranking, 10/50/100 backtest runs and
optimization remain blocked.
