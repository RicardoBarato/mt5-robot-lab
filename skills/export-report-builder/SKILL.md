name: export-report-builder
purpose: Build CSV, Markdown and optional XLSX reporting for public-safe tournament summaries.
when_to_use: Use for report schema, spreadsheet export, Markdown summaries and public report folders.
inputs: Rankings, Champion DNA, metrics, parameters, report schema and output formats.
outputs: Exported CSV, Markdown and optional XLSX files with validation notes.
hard_rules:
- do not touch ea-xau
- do not touch PayoffGrid
- do not touch ONPN11
- do not copy private files
- do not run real MT5 unless mission explicitly allows
- do not create releases/tags unless mission explicitly allows
validation: Confirm reports contain no private paths, credentials, raw MT5 logs or private reports.
handoff: Send exported artifacts to validator-release-guard.
