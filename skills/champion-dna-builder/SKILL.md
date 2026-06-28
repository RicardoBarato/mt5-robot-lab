name: champion-dna-builder
purpose: Build Champion DNA packages that explain candidate source, metrics, changes and risks.
when_to_use: Use for champion_dna.json, metrics.json, parameter_diff.md and source map work.
inputs: Candidate metadata, parameters, metrics, risk flags and export destination.
outputs: Champion DNA package and public-safe summary artifacts.
hard_rules:
- do not touch ea-xau
- do not touch PayoffGrid
- do not touch ONPN11
- do not copy private files
- do not run real MT5 unless mission explicitly allows
- do not create releases/tags unless mission explicitly allows
validation: Confirm artifacts are sanitized, numeric metrics are valid and risk is recorded not hidden.
handoff: Send packages to export-report-builder and validator-release-guard.
