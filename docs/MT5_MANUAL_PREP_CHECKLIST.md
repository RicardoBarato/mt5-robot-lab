# MT5 Manual Preparation Checklist

This checklist must be completed by the operator before any future real MT5
smoke execution.

MVP-013 Real MT5 Smoke Execution só pode ocorrer depois deste checklist.

Official credential boundary:

O MT5 Robot Lab não armazena senha, conta, servidor ou credenciais. O usuário deve fazer login diretamente no MetaTrader 5.

## Required Operator Confirmations

1. MetaTrader 5 instalado.
2. MetaEditor disponível.
3. MT5 aberto manualmente pelo usuário.
4. Conta demo conectada dentro do próprio MT5.
5. O MT5 Robot Lab não pede senha.
6. O MT5 Robot Lab não armazena conta, servidor ou credenciais.
7. Símbolo desejado visível no Market Watch.
8. Histórico do símbolo carregado.
9. Timeframe desejado disponível.
10. Operator Gate entendido.
11. Smoke real futuro limitado a 1 execução.
12. 100 backtests continuam bloqueados até outro MVP.

## What This Prep Does Not Authorize

- It does not authorize live trading.
- It does not authorize a tournament.
- It does not authorize 100 backtests.
- It does not authorize optimization.
- It does not authorize storing credentials.
- It does not promise profit or trading performance.

## Ready State

The environment is ready for the next mission only when every checklist item is
manually confirmed by the operator. If any item is missing, MVP-013 must remain
blocked.

## Local Environment Verification

After manual setup, the operator may run:

```powershell
python app\mt5_robot_lab_app.py --detect-mt5-local
```

This command only verifies local MT5 readiness and writes sanitized public
status files. It does not launch MT5, does not run Strategy Tester and does not
store account, server or credential data.
