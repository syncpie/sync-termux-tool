from textual.widgets import Static
from textual.app import ComposeResult
from config import DISCORD_INVITE

def fmt_bytes(value):
    if value is None:
        return "N/A"
    size = float(value)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.1f} {unit}"
        size /= 1024

class Metric(Static):
    pass

class Dashboard(Static):
    def compose(self) -> ComposeResult:
        yield Metric("Collecting system information...", id="overview-metrics")

    def update_snapshot(self, data):
        mem = data.get("memory", {})
        battery = data.get("battery", {})
        storage = data.get("storage", [])
        storage_text = "\n".join(
            f"{x['path']}: {fmt_bytes(x['used'])} / {fmt_bytes(x['total'])} ({x['percent']:.1f}%)"
            for x in storage
        ) or "Unavailable"
        battery_temp = battery.get("temperature_c")
        temp_text = f"{battery_temp:.1f}°C" if battery_temp is not None else "N/A"
        battery_percent = battery.get("percent")
        battery_text = f"{battery_percent}%" if battery_percent is not None else "Unavailable"
        content = (
            f"[bold #ef4444]SYNC PULSE[/]  [dim]· MADE BY SYNC[/]\n"
            f"[dim]{DISCORD_INVITE}[/]\n\n"
            f"[#f87171]CPU[/]       {data.get('cpu_percent', 0):5.1f}%   "
            f"[#f87171]CORES[/] {data.get('cpu_count', 0)}\n"
            f"[#f87171]MEMORY[/]   {fmt_bytes(mem.get('used'))} / {fmt_bytes(mem.get('total'))} "
            f"({mem.get('percent', 0):.1f}%)\n"
            f"[#f87171]BATTERY[/]  {battery_text} · {battery.get('status')} · {temp_text}\n"
            f"[dim]Battery source: {battery.get('source', 'Unknown')}[/]\n\n"
            f"[bold #ef4444]STORAGE[/]\n{storage_text}\n\n"
            f"[bold #ef4444]DEVICE[/]\n"
            f"Architecture: {data.get('device', {}).get('machine')}\n"
            f"Python: {data.get('device', {}).get('python')}\n"
            f"Kernel: {data.get('device', {}).get('kernel')}\n\n"
            f"[bold #ef4444]MADE BY SYNC[/]\n"
            f"[dim]Last update: {data.get('time', 'N/A')}[/]"
        )
        self.query_one("#overview-metrics", Metric).update(content)
