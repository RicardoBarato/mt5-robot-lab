# Real MT5 Execution Boundary

This document defines what MVP-012 allows and what remains blocked.

## Allowed in MVP-012

- Create operator gate state.
- Create approval request manifests.
- Reject or approve a gate in memory.
- Save and load gate manifests.
- Generate public-safe preview files.
- Block runners when approval is missing.
- Show UI placeholders for future real smoke requirements.

## Not Allowed in MVP-012

- Launch MT5.
- Launch Strategy Tester.
- Run a real backtest.
- Run a 100-test tournament.
- Store credentials.
- Store broker server details.
- Create `.set` files.
- Create `.ex5` files.
- Create `.exe`, `.zip`, release or tag.

## Technical Gate Conditions

Real MT5 smoke execution can be allowed only when all values are true:

```text
operator_confirmed=true
mt5_detected=true
terminal_found=true
metaeditor_found=true
real_execution_requested=true
smoke_only=true
max_backtests=1
tournament_100_run=false
no_credentials_stored=true
approval_phrase_matched=true
```

If any condition fails, runners return:

```json
{
  "status": "blocked_by_operator_gate",
  "mt5_real_run": false,
  "backtest_real_run": false,
  "reason": "Real MT5 smoke execution requires explicit operator approval."
}
```

## Future MVP-013

MVP-013 may prepare the first real MT5 smoke execution only after human review
of the gate, local MT5 setup and expected command path.

MVP-013 should still be one smoke run only, not a tournament.

## MVP-013A Hardening

MVP-013A adds additional pre-real-execution controls:

- public artifact scans across app, docs, reports, tools, tests, factory and CI;
- ignored self-test output folders so validation does not rewrite reviewed
  public artifacts;
- strict executable validation for `terminal64.exe` and `metaeditor64.exe`;
- tester config validation for approved local `.ini` or `.cfg` files only;
- redaction for local, user-home, app-data, network-share and file-URI paths;
- stronger submission-package scanning before public package validation.

These controls still do not launch MT5 and do not run Strategy Tester.

## MVP-013B Local Environment Verification

MVP-013B may detect local `terminal64.exe` and `metaeditor64.exe`, write
sanitized public readiness artifacts and report common broker symbol mappings.

It still must not launch MT5, Strategy Tester, an EA, a real backtest or a
tournament. A detected terminal is only a readiness signal. The Operator Gate
remains required before any future one-run real smoke.

## MVP-013B2 Custom Path Detection

MVP-013B2 may read ignored local config from `config/mt5.local.json` or accept
manual path arguments for safe detection only. It may also check a limited list
of likely E-drive MT5 folders.

This still does not approve or execute a smoke run. Basename, suffix and file
existence must pass before a path can be treated as detected, and all public
outputs must sanitize local paths.

## MVP-013C and MVP-014B Real Smoke Boundary

MVP-013C allowed one explicit Operator Gate real smoke. MVP-014B reused the same
one-run boundary with capture enabled.

Current recorded state:

- one-run smoke worked at execution level;
- Strategy Tester was requested once;
- no tournament was started;
- no 100-backtest run was started;
- raw local artifacts remained private;
- official Strategy Tester report capture is still not solved;
- no parseable real report exists yet.

Controlled multi-run execution is blocked until a one-run retry captures and
parses an official report.

## Strategy Tester Report Export Contract

MVP-014C prepares the next real smoke to use:

```text
Report=<private_report_base>
ReplaceReport=1
ShutdownTerminal=1
```

`Report` must target `reports/private/real_mt5_smoke/<run_id>/`, not
`reports/public`. The next smoke must search `.html`, `.htm`, `.xml`, `.csv` and
`.json` candidates, then publish only sanitized summaries.

## MT5 Close After Run Policy

Every future gated real smoke or real backtest must record:

```text
mt5_close_policy=always_after_real_run
mt5_close_attempted=<true_or_false>
mt5_closed_after_run=<true_or_false>
mt5_close_method=<method>
manual_close_required=<true_or_false>
```

Após a execução real, o MT5 será fechado para manter o ambiente limpo e evitar processos presos.

The app may close only MT5 processes started and controlled by the app. If the
terminal was already open and external to the run, the summary must record
`mt5_external_process_detected=true` and `manual_close_required=true`.

## MVP-014E Preflight Boundary

MVP-014D failed with:

```text
exit_code=3294954941
failure_stage=strategy_tester_failed_before_ea
report_file_found=false
```

MVP-014E adds a preflight layer before any retry. A future retry must block
unless all of these are true:

- `terminal64.exe` readiness confirmed;
- `metaeditor64.exe` readiness confirmed;
- Strategy Tester expert path present and safe;
- expected compiled EX5 configured and found;
- requested symbol present;
- requested timeframe supported;
- tester INI contains `[Tester]`, `Expert`, `Symbol`, `Period`,
  `Optimization=0`, `Report`, `ReplaceReport=1` and `ShutdownTerminal=1`;
- report path stays under `reports/private/real_mt5_smoke/`;
- Operator Gate approved for one run only;
- close-after-run policy is `always_after_real_run`.

If any item fails, the runner must return a hold/block result before launching
MT5. MVP-014F adds a non-executing preflight readiness command. The next allowed
real execution step is `MVP-014G One-run Real Retry After Preflight`.
