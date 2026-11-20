from textual.widgets import Static, DataTable

class TemperaturePanel(Static):
    def compose(self):
        table = DataTable(id="temperature-table")
        table.add_columns("Thermal zone", "Temperature")
        yield table

    def update_snapshot(self, data):
        table = self.query_one("#temperature-table", DataTable)
        table.clear()
        items = data.get("temperatures", [])
        for item in items:
            table.add_row(item["zone"], f"{item['temperature_c']:.1f} °C")
        if not items:
            table.add_row("Unavailable", "Android does not expose readable thermal zones")
