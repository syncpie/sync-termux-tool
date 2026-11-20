from textual.widgets import Static, DataTable

class ProcessPanel(Static):
    def compose(self):
        table = DataTable(id="process-table")
        table.add_columns("PID", "Process", "Memory", "CPU")
        yield table

    def update_snapshot(self, data):
        table = self.query_one("#process-table", DataTable)
        table.clear()
        for proc in data.get("processes", []):
            mb = proc.get("memory", 0) / (1024 * 1024)
            table.add_row(str(proc.get("pid")), str(proc.get("name"))[:30],
                          f"{mb:.1f} MB", f"{proc.get('cpu', 0):.1f}%")
