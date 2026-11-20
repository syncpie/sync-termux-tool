import json
import os
import platform
import shutil
import subprocess
import time
from pathlib import Path

try:
    import psutil
except ImportError:
    psutil = None

def read_text(path):
    try:
        return Path(path).read_text(errors="ignore").strip()
    except (OSError, PermissionError):
        return ""

def cpu_percent():
    if psutil:
        try:
            return float(psutil.cpu_percent(interval=None))
        except Exception:
            pass
    line = next((x for x in read_text("/proc/stat").splitlines() if x.startswith("cpu ")), "")
    try:
        nums = [int(x) for x in line.split()[1:]]
    except ValueError:
        return 0.0
    if len(nums) < 4:
        return 0.0
    idle = nums[3] + (nums[4] if len(nums) > 4 else 0)
    total = sum(nums)
    previous = getattr(cpu_percent, "_previous", None)
    cpu_percent._previous = (idle, total)
    if not previous:
        return 0.0
    delta_total = total - previous[1]
    delta_idle = idle - previous[0]
    return max(0.0, min(100.0, 100 * (delta_total - delta_idle) / delta_total)) if delta_total else 0.0

def memory_info():
    if psutil:
        try:
            m = psutil.virtual_memory()
            return {"total": m.total, "available": m.available, "used": m.used, "percent": m.percent}
        except Exception:
            pass
    values = {}
    for line in read_text("/proc/meminfo").splitlines():
        parts = line.split()
        if len(parts) >= 2:
            try:
                values[parts[0].rstrip(":")] = int(parts[1]) * 1024
            except ValueError:
                pass
    total = values.get("MemTotal", 0)
    available = values.get("MemAvailable", values.get("MemFree", 0))
    used = max(0, total - available)
    return {"total": total, "available": available, "used": used,
            "percent": (used / total * 100) if total else 0.0}

def _termux_battery_info():
    executable = shutil.which("termux-battery-status")
    if not executable:
        return None
    try:
        result = subprocess.run([executable], capture_output=True, text=True, timeout=3, check=True)
        payload = json.loads(result.stdout)
        percentage = payload.get("percentage")
        temperature = payload.get("temperature")
        return {
            "percent": int(percentage) if percentage is not None else None,
            "status": str(payload.get("status") or "Unknown"),
            "temperature_c": float(temperature) if temperature is not None else None,
            "health": payload.get("health"),
            "plugged": payload.get("plugged"),
            "source": "Termux:API"
        }
    except (OSError, subprocess.SubprocessError, ValueError, TypeError):
        return None

def battery_info():
    api_result = _termux_battery_info()
    if api_result and api_result.get("percent") is not None:
        return api_result

    try:
        candidates = list(Path("/sys/class/power_supply").glob("*"))
    except OSError:
        candidates = []

    for item in candidates:
        kind = read_text(item / "type").lower()
        if kind != "battery" and "battery" not in item.name.lower():
            continue
        try:
            capacity = int(read_text(item / "capacity"))
        except (ValueError, TypeError):
            capacity = None
        status = read_text(item / "status") or "Unknown"
        temperature = None
        for temp_file in ("temp", "temp_now"):
            try:
                raw = int(read_text(item / temp_file))
                temperature = raw / 1000 if raw > 1000 else raw / 10 if raw > 100 else float(raw)
                break
            except (ValueError, TypeError):
                continue
        if capacity is not None:
            return {"percent": max(0, min(100, capacity)), "status": status,
                    "temperature_c": temperature, "health": None,
                    "plugged": None, "source": "sysfs"}
    return {"percent": None, "status": "Unavailable", "temperature_c": None,
            "health": None, "plugged": None, "source": "Unavailable"}

def storage_info():
    targets = [Path.home(), Path("/storage/emulated/0")]
    results = []
    seen = set()
    for target in targets:
        try:
            key = str(target.resolve())
            if key in seen or not target.exists():
                continue
            seen.add(key)
            usage = shutil.disk_usage(target)
            results.append({"path": str(target), "total": usage.total,
                            "used": usage.used, "free": usage.free,
                            "percent": usage.used / usage.total * 100 if usage.total else 0})
        except OSError:
            continue
    return results

def temperature_info():
    results = []
    for path in Path("/sys/class/thermal").glob("thermal_zone*/temp"):
        try:
            raw = int(path.read_text().strip())
            celsius = raw / 1000 if raw > 1000 else float(raw)
            if -20 <= celsius <= 150:
                results.append({"zone": path.parent.name, "temperature_c": celsius})
        except (OSError, ValueError):
            pass
    return results[:20]

def process_info(limit=25):
    results = []
    if psutil:
        try:
            for proc in psutil.process_iter(["pid", "name", "memory_info", "cpu_percent"]):
                try:
                    info = proc.info
                    mem = info.get("memory_info")
                    results.append({"pid": info["pid"], "name": info.get("name") or "?",
                                    "memory": mem.rss if mem else 0,
                                    "cpu": info.get("cpu_percent") or 0})
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except Exception:
            pass
    if not results:
        for item in Path("/proc").iterdir():
            if item.name.isdigit():
                name = read_text(item / "comm")
                try:
                    stat = (item / "stat").read_text().split()
                    rss_pages = int((item / "statm").read_text().split()[1])
                    results.append({"pid": int(item.name), "name": name or stat[1],
                                    "memory": rss_pages * os.sysconf("SC_PAGE_SIZE"), "cpu": 0})
                except (OSError, ValueError, IndexError):
                    pass
    return sorted(results, key=lambda x: x["memory"], reverse=True)[:limit]

def network_info():
    result = []
    if psutil:
        try:
            counters = psutil.net_io_counters(pernic=True)
            for name, data in counters.items():
                result.append({"interface": name, "sent": data.bytes_sent, "received": data.bytes_recv})
            return result
        except Exception:
            pass
    for item in Path("/sys/class/net").glob("*"):
        try:
            sent = int((item / "statistics/tx_bytes").read_text())
            received = int((item / "statistics/rx_bytes").read_text())
            result.append({"interface": item.name, "sent": sent, "received": received})
        except (OSError, ValueError):
            pass
    return result

def collect_snapshot():
    memory = memory_info()
    return {
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "cpu_percent": cpu_percent(),
        "cpu_count": os.cpu_count() or 0,
        "memory": memory,
        "memory_percent": memory["percent"],
        "battery": battery_info(),
        "storage": storage_info(),
        "temperatures": temperature_info(),
        "processes": process_info(),
        "network": network_info(),
        "device": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "python": platform.python_version(),
            "android_release": os.environ.get("ANDROID_ROOT", "Android"),
            "kernel": read_text("/proc/version").split("#")[0][:100]
        }
    }
