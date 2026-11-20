# Sync Pulse

An Android Tool built with Python.

**Made by Sync** · [Discord community](https://discord.com/invite/8rUgJDpE8y)

## Features


- Termux:API battery integration with sysfs fallback
- Process list with PID and memory usage
- Network interface byte counters
- Thermal-zone readings when accessible
- SQLite resource history
- JSON diagnostic report export
- Advanced rotating JSONL logs
- One-second refresh
- No root requirement

## Install on Termux

```bash
pkg update && pkg upgrade
pkg install python git unzip termux-api
termux-setup-storage
```

Install the **Termux:API Android app** from the same trusted source as your Termux installation. The `termux-api` package alone is not enough; the Android companion app must also be installed.

```bash
cd ~/projects
unzip -o TermuxPulse.zip
cd TermuxPulse
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main.py
```

If `psutil` cannot be installed on your Android build:

```bash
python -m pip install textual
python main.py
```

## Battery troubleshooting

Test the API directly:

```bash
termux-battery-status
```

If the command is missing, install `termux-api`. If it reports that the API app is unavailable, install the Termux:API companion Android app and ensure it comes from the same signing source as Termux. Reopen Termux and run the command again.

Sync Pulse also checks `/sys/class/power_supply` as a fallback. Some Android builds restrict both sources, in which case battery percentage will show as unavailable.

## Controls

- `q` quit
- `r` refresh
- `e` export a JSON report
- `h` view history

## Logs and reports

- `logs/termuxpulse.jsonl`
- `logs/errors.jsonl`
- `reports/`

Logs rotate automatically. Reports and monitoring history remain local to the project.

## Notes

Android limits access to process details and thermal sensors. The application reports unavailable readings rather than fabricating values.
