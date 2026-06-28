# MT5 Integration Architect

Use this skill for MT5 detection, symbol discovery and Strategy Tester boundary
planning.

Rules:

- Detect `terminal64.exe` and `metaeditor64.exe` safely.
- Do not scan the whole disk aggressively.
- Do not redistribute MT5.
- Do not collect broker passwords.
- Ask users to connect demo/broker accounts inside MT5 when needed.
- Do not run real backtests without explicit authorization.
