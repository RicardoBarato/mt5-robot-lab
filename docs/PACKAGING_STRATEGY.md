# Packaging Strategy

Future packaging path:

```text
Python app -> PyInstaller bundle -> portable folder -> Inno Setup installer
```

Do not create binaries in the bootstrap. Do not bundle MT5, Codex, private
reports, credentials, real presets or raw logs.
