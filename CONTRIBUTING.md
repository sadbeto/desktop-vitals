# Contributing

Thanks for helping improve Desktop Vitals.

## Scope

Changes should preserve these properties:

- local, read-only telemetry
- no root requirement, daemon, account, or network transmission
- graceful behavior when hardware sensors are unavailable
- compatibility with the documented Python and GTK versions

## Development

On Ubuntu/Debian, install the GTK runtime dependencies:

```bash
sudo apt install python3-gi gir1.2-gtk-3.0
```

Run the checks before opening a pull request:

```bash
python3 -m compileall -q app.py install.py metrics.py test_install.py test_metrics.py
python3 -m unittest discover -v
python3 app.py --probe
```

Review and redact probe output before sharing it. UI changes should include a screenshot and the desktop/session tested.

## Pull requests

1. Create a focused branch from `main`.
2. Add or update tests and documentation with behavior changes.
3. Use a clear commit and PR title.
4. Complete the pull request checklist and wait for required checks.

Report security issues through [SECURITY.md](SECURITY.md), not a public issue.
