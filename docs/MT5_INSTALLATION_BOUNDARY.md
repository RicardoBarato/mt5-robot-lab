# MT5 Installation Boundary

MT5 Robot Lab must not bundle MetaTrader 5.

The app may detect local MT5 executables and guide the user to install or open
MT5. If a demo or broker login is required, the user performs it inside MT5.

The app must not store broker passwords, account IDs, broker server details or
MT5 logs.

## Operator Gate

MVP-012 adds a real MT5 smoke operator gate. The gate is a preview and approval
manifest system only. It does not launch MT5 and does not run Strategy Tester.

The user must log in inside MT5 if a demo or broker connection is required. The
app does not ask for credentials and does not store credentials.

Future real smoke execution requires explicit operator approval and remains
limited to one smoke run. A 100-run tournament requires a separate future MVP.
