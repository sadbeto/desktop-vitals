# Desktop Vitals

A small monochrome Linux desktop monitor. It shows CPU, RAM, disk, temperatures, network throughput, the four largest processes by resident memory, and up to two GPUs. The window is roughly square (370 × 365 px), stays behind normal windows, and refreshes every two seconds. Nothing is sent over the network.

## Requirements

- Linux with `/proc` and `/sys`; a graphical X11 desktop (tested on Xfce/Xubuntu). Wayland has not been tested.
- Python 3.8+ with GTK 3 / PyGObject system bindings. On Ubuntu/Debian, the packages are `python3-gi` and `gir1.2-gtk-3.0`. Use the system Python (`/usr/bin/python3` on Ubuntu); a Python virtualenv usually cannot import distro `gi` bindings.
- Optional: `nvidia-smi` for NVIDIA utilization, temperature, and VRAM. AMD GPUs use kernel sysfs. Intel GPU detection is supported, but load/temperature may show unavailable.

No pip packages, root privileges, daemon, or account are required at runtime.

## Run

```bash
cd desktop-vitals
/usr/bin/python3 app.py                 # primary monitor
/usr/bin/python3 app.py --monitor 1     # second monitor
/usr/bin/python3 app.py --probe         # raw JSON; no GTK needed
/usr/bin/python3 -m unittest discover -v
```

Replace `/usr/bin/python3` with the distro's system Python if needed. `--monitor` falls back to a connected monitor if the requested index is unavailable. Close with the × button. To start at login, add the absolute path to `app.py` to your desktop environment's autostart settings; this repo does not change login or system configuration for you. A maximized app hides the widget until you move or minimize it.

## What the numbers mean

- CPU utilization and network transfer rates require two samples, so the first update shows an ellipsis.
- RAM uses Linux `MemAvailable`; disk is the filesystem containing `/`.
- CPU temperature checks AMD `k10temp`, then Intel `coretemp`; fans are available only where the kernel exposes readable hwmon files. Unsupported readings show `N/A`.
- NVIDIA data comes from local `nvidia-smi` with a 2-second timeout. AMD data comes from `/sys/class/drm`; VRAM and temperature depend on driver support. With no GPU, the UI says so. At most two GPUs fit the widget.
- The process list is ranked by RSS memory, not CPU use; it may include other users' readable processes. This is a read-only monitor, not a task killer.
- CPU temperatures at or above 85°C are underlined as a visual cue, not a diagnostic threshold.

## Development

`metrics.py` collects data without GTK, `app.py` renders GTK3, and `test_metrics.py` covers sampling/GPU fallback. GitHub Actions runs unit tests and a CLI probe on Linux. No external repository code or visual theme is copied.

## References

[Conky source and feature list](https://github.com/brndnmtthws/conky) · [Xfce user discussion](https://www.reddit.com/r/xfce/comments/k2pd04/any_good_hardware_load_monitorsystem_monitor_for/) · [Conky on X](https://x.com/linux_free/status/307898702406750208) · [Conky video walkthrough](https://www.youtube.com/watch?v=s5csaCSyfoo)

MIT licensed. See [LICENSE](LICENSE).
