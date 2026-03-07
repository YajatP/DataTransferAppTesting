<img src="icons/mercs.png" height=180 style="display: block; margin-left: auto; margin-right: auto;"></img>

# 6369 Scouting Data Transfer

## 2026 Season

Transfer scouting form data from our data collection app to CSV files.  
Collects data with a serial QR/Barcode Scanner.

---

## Quick Start

### 1. Install Python

Python 3.9 or newer is required.

### 2. Install dependencies

```bash
pip install pyserial
```

> **Note:** `pyserial` is only needed for USB scanner mode. Stdin mode works with zero dependencies.

### 3. Run the script

```bash
python3 scout_transfer.py
```

That's it — plug in your scanner and start scanning QR codes.

---

## Usage Modes

### 🔌 Serial Mode (default) — USB QR Scanner

Plug in your USB QR/barcode scanner and run:

```bash
python3 scout_transfer.py
```

The script will auto-detect available serial ports and let you pick one.  
To skip the prompt, specify the port directly:

```bash
python3 scout_transfer.py --port /dev/cu.usbserial-1420
```

You can also set a custom baud rate (default is 115200):

```bash
python3 scout_transfer.py --port COM3 --baud 9600
```

Once running, just scan QR codes — each scan is automatically parsed, checked for duplicates, and saved to the database.

Press **Ctrl+C** to export all data to CSV and exit.

### ⌨️ Stdin Mode — No Scanner Required

For testing or manual entry, paste QR data lines directly:

```bash
python3 scout_transfer.py --stdin
```

Type or paste `||`-delimited lines at the `scan>` prompt. Example:

```
match||9999||RonCollins||blue||1||middle||true||0||0||0||0||0||0||0||0||0||0||0||0||0||0||0||0||0||0||0||0||0||0||0||0||0||0||none||0||false||false||false||false||false||0||false||
```

Press **Ctrl+D** or **Ctrl+C** to export and quit.

### 📤 Export Mode — CSV Export Only

To export an existing database to CSV without scanning any new data:

```bash
python3 scout_transfer.py --export
```

### Custom Database File

By default the database is `scouting.db` in the current directory. To use a different file:

```bash
python3 scout_transfer.py --db my_event.db
```

---

## Terminal Feedback

The script gives you live visual feedback in the terminal:

| Symbol | Meaning |
|--------|---------|
| ✓ (green) | Scan successfully saved |
| ⚠ (yellow) | Duplicate scan — skipped |
| ✗ (red) | Error (unknown form, field mismatch, etc.) |

A **live status bar** at the bottom shows running totals for pit/match entries, duplicates, errors, and the last scan timestamp.

---

## QR Data Format

The QR codes from the Android collection app encode data as **`||`-delimited** plain text strings:

```
pit||9999||RonCollins,RonCollins||null||null||null||false||...
match||9999||RonCollins||blue||1||middle||true||0||0||...
```

- First field is always the **form name** (`pit` or `match`)
- Second field is always the **team number**
- Remaining fields match the order defined in the `FIELDS` dict inside `scout_transfer.py`

The script automatically converts these to proper CSV on export.

---

## Output Files

On exit (or with `--export`), the script creates:

- `pit_export.csv` — all pit scouting data
- `match_export.csv` — all match scouting data

---

## All CLI Options

```
python3 scout_transfer.py --help
```

| Flag | Description | Default |
|------|-------------|---------|
| `--port` | Serial port for USB scanner | Auto-detect |
| `--baud` | Baud rate | `115200` |
| `--db` | SQLite database file | `scouting.db` |
| `--stdin` | Read from keyboard/pipe instead of serial | Off |
| `--export` | Export existing DB to CSV and quit | Off |
