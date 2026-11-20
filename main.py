import argparse
import asyncio
import logging
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Header, Footer, TabbedContent, TabPane, RichLog, Static
from config import APP_NAME, REFRESH_SECONDS, DISCORD_INVITE
from core.collector import collect_snapshot
from core.history import History
from core.reports import export_report
from loggingx.setup import configure_logging
from startup.fire import run_fire_splash
from ui.dashboard import Dashboard
from ui.processes import ProcessPanel
from ui.network import NetworkPanel
from ui.temperature import TemperaturePanel

logger = logging.getLogger("termuxpulse.app")

class BrandFooter(Static):
    def render(self):
        return f"[bold #ef4444]MADE BY SYNC[/]  [#888888]·[/]  [#ef4444]{DISCORD_INVITE}[/]"

class SyncPulse(App):
    TITLE = APP_NAME
    SUB_TITLE = "MADE BY SYNC"
    CSS_PATH = "ui/theme.tcss"
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh_now", "Refresh"),
        Binding("e", "export", "Export report"),
        Binding("h", "history", "History"),
    ]

    def __init__(self):
        super().__init__()
        self.snapshot = {}
        self.history = History()

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent(initial="overview"):
            with TabPane("Overview", id="overview"):
                yield Dashboard(id="dashboard")
            with TabPane("Processes", id="processes"):
                yield ProcessPanel(id="process-panel")
            with TabPane("Network", id="network"):
                yield NetworkPanel(id="network-panel")
            with TabPane("Temperature", id="temperature"):
                yield TemperaturePanel(id="temperature-panel")
            with TabPane("History", id="history"):
                yield RichLog(id="history-log", wrap=True, markup=True)
        yield BrandFooter()
        yield Footer()

    async def on_mount(self):
        logger.info("Sync Pulse dashboard mounted", extra={"event": "dashboard_mounted"})
        self.set_interval(REFRESH_SECONDS, self.refresh_data)
        await self.refresh_data()

    async def refresh_data(self):
        try:
            self.snapshot = await asyncio.to_thread(collect_snapshot)
            self.history.add(self.snapshot)
            self.query_one("#dashboard", Dashboard).update_snapshot(self.snapshot)
            self.query_one("#process-panel", ProcessPanel).update_snapshot(self.snapshot)
            self.query_one("#network-panel", NetworkPanel).update_snapshot(self.snapshot)
            self.query_one("#temperature-panel", TemperaturePanel).update_snapshot(self.snapshot)
            if self.snapshot.get("battery", {}).get("percent") is None:
                logger.warning("Battery percentage unavailable", extra={
                    "event": "battery_unavailable",
                    "details": "Install the Termux:API app and termux-api package"
                })
            logger.debug("System snapshot collected", extra={"event": "snapshot_collected"})
        except Exception:
            logger.exception("System refresh failed", extra={"event": "refresh_failed"})
            self.notify("Refresh failed. Check logs/ for details.", severity="error")

    def action_refresh_now(self):
        logger.info("Manual refresh requested", extra={"event": "manual_refresh"})
        self.run_worker(self.refresh_data(), exclusive=True)

    def action_export(self):
        try:
            path = export_report(self.snapshot, self.history.recent())
            logger.info("Diagnostic report exported", extra={"event": "report_exported", "details": path})
            self.notify(f"Report exported: {path}", title=APP_NAME)
        except Exception:
            logger.exception("Report export failed", extra={"event": "report_export_failed"})
            self.notify("Export failed. Check logs/ for details.", severity="error")

    def action_history(self):
        log = self.query_one("#history-log", RichLog)
        log.clear()
        for item in self.history.recent(60):
            battery = item.get("battery", {}).get("percent")
            log.write(
                f"[#ef4444]{item['time']}[/]  CPU {item.get('cpu_percent', 0):.1f}%  "
                f"RAM {item.get('memory_percent', 0):.1f}%  Battery {battery if battery is not None else 'N/A'}%"
            )
        logger.info("History viewed", extra={"event": "history_viewed"})

    def on_unmount(self):
        logger.info("Sync Pulse stopped", extra={"event": "application_stopped"})

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="sync-pulse")
    parser.add_argument("--no-splash", action="store_true", help="Skip startup animation")
    parser.add_argument("--log-level", choices=("DEBUG", "INFO", "WARNING", "ERROR"), default="INFO")
    args = parser.parse_args()
    configure_logging(level=getattr(logging, args.log_level))
    if not args.no_splash:
        logger.info("Starting animated splash", extra={"event": "startup_splash"})
        run_fire_splash()
    logger.info("Starting Sync Pulse dashboard", extra={"event": "dashboard_start"})
    SyncPulse().run()
