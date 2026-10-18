# Desktop Vitals

[![Tests](https://github.com/sadbeto/desktop-vitals/actions/workflows/tests.yml/badge.svg)](https://github.com/sadbeto/desktop-vitals/actions/workflows/tests.yml)
[![CodeQL](https://github.com/sadbeto/desktop-vitals/actions/workflows/codeql.yml/badge.svg)](https://github.com/sadbeto/desktop-vitals/actions/workflows/codeql.yml)
[![Latest release](https://img.shields.io/github/v/release/sadbeto/desktop-vitals)](https://github.com/sadbeto/desktop-vitals/releases/latest)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A small monochrome Linux desktop monitor for CPU, RAM, disk, temperatures, aggregate network I/O, the four largest processes by resident memory, and up to two GPUs. The roughly square window stays behind normal windows and refreshes every two seconds. The app does not open network connections or transmit telemetry.

## Requirements

- Linux with `/proc` and `/sys`; a graphical X11 desktop (tested on Xfce/Xubuntu). Wayland has not been tested.
- Python 3.10+ with GTK 3 / PyGObject system bindings. On Ubuntu/Debian, install `python3-gi` and `gir1.2-gtk-3.0`. Use the distro's system Python; a virtual environment usually cannot import distro `gi` bindings.
- Optional: `nvidia-smi` for NVIDIA utilization, temperature, and VRAM. AMD GPUs use kernel sysfs. Intel GPU detection is supported, but load and temperature may be unavailable.

No pip packages, root privileges, daemon, or account are required at runtime.

## Install for your user

Clone the repository or download and extract the [latest release](https://github.com/sadbeto/desktop-vitals/releases/latest), then run from its root:

```bash
cd desktop-vitals
python3 install.py             # monitor index 0
python3 install.py --monitor 1 # monitor index 1
```

Open **Desktop Vitals** from the applications menu. The installer uses the Python interpreter that launched it and copies the app into `$XDG_DATA_HOME/desktop-vitals` (default `~/.local/share/desktop-vitals`), with a launcher and icon under the same data directory. It does not change autostart, services, packages, or system settings. Run the installer again after updates, then reopen the widget.

Uninstall only the user-local files created by the installer:

```bash
python3 install.py --uninstall
```

## Run from the checkout

```bash
cd desktop-vitals
python3 app.py                 # monitor index 0
python3 app.py --monitor 1     # monitor index 1
python3 app.py --probe         # raw JSON; GTK is not required
python3 -m unittest discover -v
```

`--monitor` clamps unavailable indexes to a connected monitor. Close the widget with the × button. For desktop autostart, configure the full command `python3 /absolute/path/to/desktop-vitals/app.py`; the repository does not modify login settings. On the tested Xfce setup, maximized applications cover the keep-below widget.

## What the numbers mean

- CPU utilization and network rates require two samples, so the first update shows an ellipsis.
- `RX` and `TX` aggregate all non-loopback interfaces. VPNs, containers, bridges, and virtual interfaces can make these totals larger than Internet-only traffic.
- RAM uses Linux `MemAvailable`; disk is the filesystem containing `/`.
- CPU temperature checks AMD `k10temp`, then Intel `coretemp`. Fan readings currently target ASUS hwmon labels; each available CPU or GPU fan is shown independently.
- NVIDIA data comes from local `nvidia-smi` with a two-second timeout. AMD data comes from `/sys/class/drm`; readings depend on driver support. At most two GPUs fit the widget.
- The process list is ranked by RSS memory, not CPU use. It may include other users' readable processes. The monitor never kills processes.
- CPU temperatures at or above 85°C are underlined as a visual cue, not a diagnostic threshold.

The `--probe` output includes process names and PIDs, GPU models, and live telemetry. Review and redact it before posting publicly.

## Development and security

`metrics.py` collects telemetry without GTK, `app.py` renders GTK3, and `install.py` manages user-local installation. `test_metrics.py` covers sampling and GPU fallback; `test_install.py` covers launcher generation, copy/update behavior, and uninstall. GitHub Actions tests Python 3.10 and a current Python release, runs a CLI probe, and performs CodeQL analysis.

See [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request. Report vulnerabilities privately as described in [SECURITY.md](SECURITY.md).

## References

[Conky source and feature list](https://github.com/brndnmtthws/conky) · [Xfce user discussion](https://www.reddit.com/r/xfce/comments/k2pd04/any_good_hardware_load_monitorsystem_monitor_for/) · [Conky video walkthrough](https://www.youtube.com/watch?v=s5csaCSyfoo)

MIT licensed. See [LICENSE](LICENSE).
