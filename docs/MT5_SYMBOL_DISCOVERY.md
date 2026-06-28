# MT5 Symbol Discovery

The product should detect symbols from the local MT5 terminal when available.

Conceptual mapping:

| Asset | Candidate symbols |
| --- | --- |
| Gold / XAU | `XAUUSD`, `XAUUSD.`, `XAUUSDm`, `GOLD`, `GOLDmicro` |
| Nasdaq / USTEC | `USTEC`, `USTEC.cash`, `NAS100`, `US100`, `US100.cash` |
| Dow / US30 | `US30`, `US30.cash`, `DJ30`, `WallStreet30` |
| Bitcoin | `BTCUSD`, `BTCUSD.`, `BTCUSDm`, `BTCUSD.cash` |

If symbols or history are unavailable, the app should ask the user to open MT5
and connect a demo account. Passwords are not stored.

## Operator Gate Boundary

Symbol discovery is separate from real execution. Detection can identify common
broker mappings and future MT5 availability, but it does not approve a real MT5
smoke run.

MVP-012 requires a separate operator gate before any future real local smoke
execution. The gate keeps CI safe and blocks 100-run tournaments by default.
