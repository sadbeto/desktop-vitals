"""Read local telemetry from /proc and /sys without privileged access."""
import os
from pathlib import Path


def sensor(chip, kind, label=None):
    for d in Path('/sys/class/hwmon').glob('hwmon*'):
        try:
            if (d / 'name').read_text().strip() != chip:
                continue
            for item in sorted(d.glob(kind + '*_input')):
                if label and (item.with_name(item.name.replace('_input', '_label'))).read_text().strip() != label:
                    continue
                n = float(item.read_text().strip())
                return n / 1000 if kind == 'temp' else n
        except (OSError, ValueError):
            continue
    return None


def cpu():
    try:
        fields = list(map(int, Path('/proc/stat').read_text().splitlines()[0].split()[1:]))
        return sum(fields), fields[3] + fields[4]
    except (OSError, ValueError, IndexError):
        return None


def memory():
    try:
        data = {k: int(v.split()[0]) for k, v in (line.split(':', 1) for line in Path('/proc/meminfo').read_text().splitlines())}
        used = data['MemTotal'] - data['MemAvailable']
        return 100 * used / data['MemTotal'], used / 1048576, data['MemTotal'] / 1048576
    except (OSError, ValueError, KeyError, ZeroDivisionError):
        return None


def network():
    try:
        pairs = [line.split(':', 1) for line in Path('/proc/net/dev').read_text().splitlines()[2:]]
        nums = [v.split() for name, v in pairs if name.strip() != 'lo']
        return sum(int(v[0]) for v in nums), sum(int(v[8]) for v in nums)
    except (OSError, ValueError, IndexError):
        return None


def processes(limit=4):
    rows = []
    for p in Path('/proc').glob('[0-9]*'):
        try:
            rss = next((int(line.split()[1]) for line in (p / 'status').read_text().splitlines() if line.startswith('VmRSS:')), 0)
            if rss:
                rows.append((rss, (p / 'comm').read_text().strip()[:22], p.name))
        except (OSError, ValueError, IndexError):
            continue
    return [{'name': name, 'mib': round(rss / 1024), 'pid': pid} for rss, name, pid in sorted(rows, reverse=True)[:limit]]


def gpu_devices():
    """Best-effort GPU telemetry. Missing drivers/readings stay None."""
    import shutil
    import subprocess

    devices = []
    nvidia_seen = False
    if shutil.which('nvidia-smi'):
        try:
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=name,utilization.gpu,temperature.gpu,memory.used,memory.total',
                 '--format=csv,noheader,nounits'], capture_output=True, text=True,
                timeout=2, check=True)
            for line in result.stdout.splitlines():
                fields = [part.strip() for part in line.split(',')]
                if len(fields) != 5:
                    continue
                def number(value):
                    try:
                        return float(value)
                    except ValueError:
                        return None
                devices.append({'name': fields[0], 'vendor': 'NVIDIA', 'usage': number(fields[1]),
                                'temp': number(fields[2]), 'vram_used': number(fields[3]),
                                'vram_total': number(fields[4])})
                nvidia_seen = True
        except (OSError, subprocess.SubprocessError):
            pass

    for card in sorted(Path('/sys/class/drm').glob('card[0-9]*')):
        vendor_path = card / 'device/vendor'
        try:
            vendor = vendor_path.read_text().strip().lower()
        except OSError:
            continue
        if vendor == '0x10de':
            if not nvidia_seen:
                devices.append({'name': 'NVIDIA GPU', 'vendor': 'NVIDIA', 'usage': None,
                                'temp': None, 'vram_used': None, 'vram_total': None})
            continue
        if vendor == '0x1002':
            base = card / 'device'
            def mb(path):
                value = read_number(path)
                return value / 1048576 if value is not None else None
            devices.append({'name': 'AMD Radeon', 'vendor': 'AMD',
                            'usage': read_number(base / 'gpu_busy_percent'),
                            'temp': sensor('amdgpu', 'temp', 'edge') or sensor('amdgpu', 'temp'),
                            'vram_used': mb(base / 'mem_info_vram_used'),
                            'vram_total': mb(base / 'mem_info_vram_total')})
        elif vendor == '0x8086':
            devices.append({'name': 'Intel GPU', 'vendor': 'Intel', 'usage': None,
                            'temp': None, 'vram_used': None, 'vram_total': None})
    return devices


def read_number(path):
    try:
        return float(Path(path).read_text().strip())
    except (OSError, ValueError):
        return None


class Sampler:
    def __init__(self):
        self.last_cpu = self.last_net = self.last_time = None

    def sample(self):
        import time
        c, n, now = cpu(), network(), time.monotonic()
        usage = speeds = None
        if c and self.last_cpu:
            total = c[0] - self.last_cpu[0]
            if total > 0:
                usage = max(0, min(100, 100 * (total - (c[1] - self.last_cpu[1])) / total))
        if n and self.last_net and self.last_time and now > self.last_time:
            dt = now - self.last_time
            speeds = tuple(max(0, (x - y) / dt) for x, y in zip(n, self.last_net))
        self.last_cpu, self.last_net, self.last_time = c, n, now
        fs = os.statvfs('/')
        capacity, free = fs.f_blocks * fs.f_frsize, fs.f_bavail * fs.f_frsize
        return {'cpu': usage, 'memory': memory(),
                'cpu_temp': sensor('k10temp', 'temp', 'Tctl') or sensor('k10temp', 'temp') or sensor('coretemp', 'temp', 'Package id 0') or sensor('coretemp', 'temp'),
                'gpu_temp': sensor('amdgpu', 'temp', 'edge') or sensor('amdgpu', 'temp'),
                'cpu_fan': sensor('asus', 'fan', 'cpu_fan') or sensor('asus', 'fan'),
                'gpu_fan': sensor('asus', 'fan', 'gpu_fan'),
                'disk': (100 * (capacity-free)/capacity, (capacity-free)/2**30, capacity/2**30) if capacity else None,
                'network': speeds, 'processes': processes(), 'gpus': gpu_devices()}
