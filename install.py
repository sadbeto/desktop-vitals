#!/usr/bin/python3
"""Install a private application copy and launcher; never requires root."""
import argparse
import os
from pathlib import Path
import shutil
import sys

FILES = ('app.py', 'metrics.py', 'LICENSE', 'assets/desktop-vitals.svg')


def exec_quote(value):
    """Escape a single Desktop Entry Exec argument (not shell syntax)."""
    value = str(value)
    for old, new in (('\\', '\\\\'), ('"', '\\"'), ('`', '\\`'), ('$', '\\$'), ('%', '%%')):
        value = value.replace(old, new)
    return '"' + value.replace('\\', '\\\\') + '"'


def install(source, data_home, monitor=0, python=None):
    source, data_home = Path(source), Path(data_home).resolve()
    python = Path(python or sys.executable).resolve()
    app = data_home / 'desktop-vitals'
    for relative in FILES:
        if not (source / relative).is_file():
            raise FileNotFoundError(source / relative)
    for relative in FILES:
        target = app / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / relative, target)
    icon = data_home / 'icons/hicolor/scalable/apps/desktop-vitals.svg'
    icon.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source / 'assets/desktop-vitals.svg', icon)
    launcher = data_home / 'applications/desktop-vitals.desktop'
    launcher.parent.mkdir(parents=True, exist_ok=True)
    launcher.write_text(
        '[Desktop Entry]\nType=Application\nName=Desktop Vitals\n'
        'Comment=Local CPU, GPU, memory and temperature monitor\n'
        f'Exec={exec_quote(python)} {exec_quote(app / "app.py")} --monitor {monitor}\n'
        'Icon=desktop-vitals\nTerminal=false\nCategories=System;Monitor;\n'
        'Keywords=CPU;GPU;RAM;Temperature;\nStartupNotify=false\n', encoding='utf-8')
    return launcher


def uninstall(data_home):
    """Remove only files created by this user-local installer."""
    data_home = Path(data_home).resolve()
    shutil.rmtree(data_home / 'desktop-vitals', ignore_errors=True)
    for target in (
        data_home / 'applications/desktop-vitals.desktop',
        data_home / 'icons/hicolor/scalable/apps/desktop-vitals.svg',
    ):
        try:
            target.unlink()
        except FileNotFoundError:
            pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--monitor', type=int, default=0)
    parser.add_argument('--uninstall', action='store_true')
    args = parser.parse_args()
    if args.monitor < 0:
        parser.error('--monitor must be non-negative')
    configured = os.environ.get('XDG_DATA_HOME')
    data = Path(configured) if configured else Path.home() / '.local/share'
    if not data.is_absolute():
        parser.error('XDG_DATA_HOME must be absolute')
    if args.uninstall:
        uninstall(data)
        print('Desktop Vitals removed from', data)
    else:
        print(install(Path(__file__).resolve().parent, data, args.monitor))


if __name__ == '__main__':
    main()
