# Grand MVP Factory

The Grand MVP Factory is the operating system for larger MT5 Robot Lab product
batches. It keeps the roadmap, queue, prompt generation and validation rules in
one public-safe location.

## Commands

```powershell
python factory\mvp_factory.py --self-test
python factory\mvp_factory.py --list
python factory\mvp_factory.py --next
python factory\mvp_factory.py --show MVP-001
python factory\mvp_factory.py --generate-prompt MVP-001
python factory\mvp_factory.py --mark-status MVP-001 planned
```

The factory does not execute Codex, MT5, Strategy Tester, backtests, releases or
packaging. It only reads queue metadata, validates it and prints operator-ready
prompts.
