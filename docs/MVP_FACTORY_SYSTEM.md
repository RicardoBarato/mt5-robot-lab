# MVP Factory System

The MVP Factory is implemented under `factory/`.

## Files

- `factory/mvp_queue.json`: canonical queue of the first 10 Grand MVPs.
- `factory/mvp_status.json`: lightweight status map.
- `factory/mvp_factory.py`: stdlib-only queue utility.
- `factory/templates/grand_mvp_prompt_template.md`: prompt template.
- `factory/templates/final_report_template.md`: final report template.

## Commands

```powershell
python factory\mvp_factory.py --self-test
python factory\mvp_factory.py --list
python factory\mvp_factory.py --next
python factory\mvp_factory.py --show MVP-001
python factory\mvp_factory.py --generate-prompt MVP-001
python factory\mvp_factory.py --mark-status MVP-001 planned
```

## Boundaries

The factory does not execute Codex, MT5, Strategy Tester, real backtests,
installers, release creation or tag creation. It only manages public-safe
planning metadata.
