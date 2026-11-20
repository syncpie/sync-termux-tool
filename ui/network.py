from textual.widgets import Static, DataTable

def fmt_bytes(value):
    size = float(value)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.1f} {unit}"
        size /= 1024

class NetworkPanel(Static):
    def compose(self):
        table = DataTable(id="network-table")
        table.add_columns("Interface", "Sent", "Received")
        yield table

    def update_snapshot(self, data):
        table = self.query_one("#network-table", DataTable)
        table.clear()
        for item in data.get("network", []):
            table.add_row(item["interface"], fmt_bytes(item["sent"]), fmt_bytes(item["received"]))
