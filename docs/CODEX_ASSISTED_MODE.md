# Codex Assisted Mode

Codex Assisted Mode is optional.

The app may prepare a mission packet and detect whether Codex CLI is available.
It must not install Codex, log in to Codex or execute Codex without explicit user
authorization.

Reports should record:

- `intelligence_mode`;
- `codex_used`;
- `codex_authorized`;
- `mutation_mode`;
- `seed_family`.

## Intelligence Mode Screen

```text
Tela: Modo de Inteligencia

[x] Local automatico
    Testa variacoes programadas sem usar IA externa.

[ ] Codex assisted
    Usa Codex para propor alteracoes MQL5 avancadas.
    Requer login/autorizacao da conta ChatGPT.

[ ] Seeds only
    Testa apenas robos-base incluidos.
```

`local_auto` is the default. `codex_assisted` is optional and requires explicit
authorization. `seeds_only` runs included base robots only.
