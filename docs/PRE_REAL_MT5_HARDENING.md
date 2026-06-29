# Pre-Real MT5 Safety Hardening

MVP-013A hardens the project before any future real MetaTrader 5 smoke
execution. It is a preparation step only.

## Scope

- Real MT5 run: false
- Real Strategy Tester backtest: false
- 100-run tournament: false
- Installer or portable package: false
- Stored broker login details: false

## Public Artifact Guard

The publication guard now scans public and versioned text artifacts across:

- `reports/public/`
- `app/`
- `tools/`
- `tests/`
- `docs/`
- `factory/`
- `.github/workflows/`

It reports unsafe public artifacts, private path leaks, local machine paths,
forbidden compiled or preset files and sensitive runtime values. Policy and test
wording may mention blocked terms only as denylist or safety documentation.

## Self-Test Output Boundary

Self-tests now write runtime artifacts under ignored `runs/self_tests/` folders.
They must not update tracked public reports during CI or local validation.

The versioned `reports/public/` directory is reserved for reviewed public sample
artifacts and mission reports.

## MT5 Path Validation

Before any future real execution, paths must pass these checks:

- terminal executable basename is exactly `terminal64.exe`;
- MetaEditor executable basename is exactly `metaeditor64.exe`;
- executable suffix is `.exe`;
- file exists locally;
- tester config is an approved local `.ini` or `.cfg`;
- tester config is inside approved local config or ignored run folders;
- `.set`, `.tst`, `.ex5` and environment files are rejected.

If the Operator Gate blocks execution, the runner returns a blocked JSON status
without validating or launching a real terminal command.

## Path Redaction

Public-facing output must replace local path material with placeholders:

- `<USER_HOME>`
- `<LOCAL_APPDATA>`
- `<APPDATA>`
- `<WINDOWS_PATH_REDACTED>`
- `<NETWORK_PATH_REDACTED>`
- `<FILE_URI_REDACTED>`

This applies to user-home paths, local app-data paths, network shares, file URIs
and environment-placeholder based paths.

## Submission Package Scan

Submission packages are scanned for forbidden files, private local paths, file
URIs and sensitive runtime terms before they can be marked valid.

## CI Alignment

The public CI workflow now runs compile checks, unit tests, app self-tests,
operator-gate self-tests, publication guard, factory self-test, whitespace check
and working-tree check.
