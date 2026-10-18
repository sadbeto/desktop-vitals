#!/usr/bin/python3
"""Square monochrome desktop telemetry for Xfce."""
import argparse
import json
import textwrap
from pathlib import Path
from metrics import Sampler


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--probe', action='store_true')
    ap.add_argument('--monitor', type=int, default=0, help='display index (default: 0)')
    args = ap.parse_args()
    if args.probe:
        print(json.dumps(Sampler().sample(), indent=2))
        return

    import gi
    gi.require_version('Gtk', '3.0')
    gi.require_version('Gdk', '3.0')
    from gi.repository import Gdk, GLib, Gtk

    css = b'''window { background: #080808; border: 1px solid #777; border-radius: 0; }
    label { font-family: monospace; font-size: 11px; color: #f0f0f0; }
    .title { font-size: 14px; font-weight: bold; }
    .dim { color: #a0a0a0; }
    .section { color: #b9b9b9; font-size: 10px; font-weight: bold; }
    .warn { color: #fff; font-weight: bold; text-decoration: underline; }
    button { background: transparent; color: #aaa; border: 0; box-shadow: none; min-width: 20px; min-height: 20px; padding: 0; }
    button:hover { background: #333; color: #fff; }
    separator { background: #555; min-width: 1px; min-height: 1px; }
    '''
    provider = Gtk.CssProvider()
    provider.load_from_data(css)
    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def txt(content, style=None):
        item = Gtk.Label(label=content)
        item.set_xalign(0)
        if style:
            item.get_style_context().add_class(style)
        return item

    icon = Path(__file__).resolve().parent / 'assets' / 'desktop-vitals.svg'
    win = Gtk.Window(title='Desktop Vitals')
    if icon.is_file():
        win.set_icon_from_file(str(icon))
    win.set_default_size(370, 365)
    win.set_resizable(False)
    win.set_type_hint(Gdk.WindowTypeHint.UTILITY)
    win.set_skip_taskbar_hint(True)
    win.set_skip_pager_hint(True)
    win.stick()
    win.connect('destroy', Gtk.main_quit)
    display = Gdk.Display.get_default()
    monitor = display.get_monitor(max(0, min(args.monitor, display.get_n_monitors() - 1)))
    area = monitor.get_geometry()
    win.move(area.x + area.width - 390, area.y + 60)

    root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=7)
    root.set_margin_top(12); root.set_margin_bottom(12)
    root.set_margin_start(13); root.set_margin_end(13)
    win.add(root)
    header = Gtk.Box(spacing=6)
    header.pack_start(txt('SYSTEM  /  LIVE', 'title'), True, True, 0)
    close = Gtk.Button(label='×')
    close.set_tooltip_text('Close widget')
    close.connect('clicked', lambda _: win.destroy())
    header.pack_end(close, False, False, 0)
    root.pack_start(header, False, False, 0)
    root.pack_start(Gtk.Separator(), False, False, 1)

    grid = Gtk.Grid()
    grid.set_column_spacing(12)
    grid.set_row_spacing(10)
    grid.set_column_homogeneous(True)
    grid.set_row_homogeneous(False)
    root.pack_start(grid, True, True, 0)

    def section(title, col, row):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        box.pack_start(txt(title, 'section'), False, False, 0)
        box.pack_start(Gtk.Separator(), False, False, 0)
        grid.attach(box, col, row, 1, 1)
        return box

    def metric(box, name):
        line = Gtk.Box(spacing=2)
        key = txt(name, 'dim')
        value = txt('—')
        value.set_xalign(1)
        line.pack_start(key, True, True, 0)
        line.pack_end(value, False, False, 0)
        box.pack_start(line, False, False, 0)
        return value, key

    performance = section('PERFORMANCE', 0, 0)
    cpu, _ = metric(performance, 'CPU')
    ram, _ = metric(performance, 'RAM')
    disk, _ = metric(performance, 'DISK')

    graphics = section('GRAPHICS', 1, 0)
    graphics.set_spacing(2)
    gpu_rows = []
    for _ in range(2):
        gpu_name = txt('—', 'dim')
        gpu_value = txt('')
        graphics.pack_start(gpu_name, False, False, 0)
        graphics.pack_start(gpu_value, False, False, 0)
        gpu_rows.append((gpu_name, gpu_value))

    details = section('SYSTEM / NETWORK', 0, 1)
    cpu_temp, _ = metric(details, 'CPU TEMP')
    fan, _ = metric(details, 'FANS')
    down, _ = metric(details, 'RX')
    up, _ = metric(details, 'TX')
    mem_detail = txt('—', 'dim')
    details.pack_end(mem_detail, False, False, 0)

    tasks = section('TOP MEMORY', 1, 1)
    proc_rows = [metric(tasks, '—') for _ in range(4)]
    root.pack_end(txt('LOCAL  •  2 SEC REFRESH', 'dim'), False, False, 0)
    sampler = Sampler()

    def human_rate(n):
        if n is None:
            return '—'
        for suffix in ('B/s', 'K/s', 'M/s', 'G/s'):
            if n < 1024 or suffix == 'G/s':
                return f'{n:.0f}{suffix}'
            n /= 1024

    def refresh():
        try:
            d = sampler.sample()
            cpu.set_text(f"{d['cpu']:.0f}%" if d['cpu'] is not None else '…')
            m, z = d['memory'], d['disk']
            ram.set_text(f'{m[0]:.0f}%' if m else 'N/A')
            disk.set_text(f'{z[0]:.0f}%' if z else 'N/A')
            mem_detail.set_text(f'{m[1]:.1f} / {m[2]:.0f} GiB RAM' if m else 'RAM unavailable')
            value = d['cpu_temp']
            cpu_temp.set_text(f'{value:.0f}°C' if value is not None else 'N/A')
            context = cpu_temp.get_style_context()
            (context.add_class if value is not None and value >= 85 else context.remove_class)('warn')
            for (name, reading), gpu in zip(gpu_rows, d['gpus'][:2] + [None] * 2):
                if not gpu:
                    name.set_text('NO GPU DETECTED' if not d['gpus'] else '')
                    reading.set_text('')
                    continue
                name.set_text('\n'.join(textwrap.wrap(gpu['name'], width=20, break_long_words=True)))
                name.set_tooltip_text(gpu['name'])
                usage = f"{gpu['usage']:.0f}%" if gpu['usage'] is not None else '—%'
                temp = f"{gpu['temp']:.0f}°" if gpu['temp'] is not None else '—°'
                used, total = gpu['vram_used'], gpu['vram_total']
                vram = f'{used / 1024:.1f}/{total / 1024:.0f}G' if used is not None and total and total >= 1024 else (f'{used:.0f}/{total:.0f}M' if used is not None and total else 'VRAM —')
                reading.set_text(f'{usage}  {temp}  {vram}')
            a, b = d['cpu_fan'], d['gpu_fan']
            readings = []
            if a is not None:
                readings.append(f'CPU {a:.0f}')
            if b is not None:
                readings.append(f'GPU {b:.0f}')
            fan.set_text(' / '.join(readings) if readings else 'N/A')
            net = d['network']
            down.set_text(human_rate(net[0]) if net else '…')
            up.set_text(human_rate(net[1]) if net else '…')
            for (value, name), proc in zip(proc_rows, d['processes'] + [None] * 4):
                name.set_text(proc['name'][:12] if proc else '—')
                value.set_text(f"{proc['mib']}M" if proc else '')
        except (OSError, ValueError) as exc:
            mem_detail.set_text(f'read error: {exc}')
        return True

    win.show_all()
    win.get_window().set_keep_below(True)
    refresh()
    GLib.timeout_add_seconds(2, refresh)
    Gtk.main()


if __name__ == '__main__':
    main()
