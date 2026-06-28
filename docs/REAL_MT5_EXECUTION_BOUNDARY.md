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
