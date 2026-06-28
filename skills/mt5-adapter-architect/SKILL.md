name: mt5-adapter-architect
purpose: Design MT5 adapter boundaries before any real MT5 execution is allowed.
when_to_use: Use for MT5 detection, terminal/metaeditor path handling and future real smoke planning.
inputs: MT5 boundary docs, app config, detection requirements and user consent rules.
outputs: Adapter architecture, safety gates, test plan and no-credential policy.
hard_rules:
- do not touch ea-xau
- do not touch PayoffGrid
- do not touch ONPN11
- do not copy private files
- do not run real MT5 unless mission explicitly allows
- do not create releases/tags unless mission explicitly allows
validation: Confirm no real backtest, no stored credentials and no bundled MT5 installer.
handoff: Send safe stubs to symbol-discovery-engineer or validator-release-guard.
