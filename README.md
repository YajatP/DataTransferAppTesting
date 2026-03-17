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

---

## Desktop App (GUI)

A standalone desktop app with a dark-themed UI, live status indicators, and a built-in tablet manager.

### Features

- **Scanner Connection** — Connect to USB QR scanners with port/baud selection and live status dots
- **Manual Entry** — Paste QR data directly (no scanner needed)
- **Live Scan Log** — Scrolling feed with ✓/⚠/✗ icons and timestamps
- **Data Tables** — Tabbed view of all pit, match, and auton data
- **CSV Export** — One-click export with success confirmation
- **Tablet Manager** — Fetch scouting app releases from GitHub, download APKs, and install to Android tablets via ADB

### Running the GUI (from source)

```bash
# Activate the project's virtual environment
source .venv/bin/activate

# Launch the GUI
python scout_transfer_gui.py
```

### Pre-Built App

#### macOS

1. Download `ScoutTransfer-macOS.zip` from the [Releases](../../releases) page (or GitHub Actions artifacts)
2. Unzip and move `ScoutTransfer.app` to your Applications folder
3. If macOS blocks the app, run: `xattr -cr ScoutTransfer.app`
4. Double-click to open

#### Windows

1. Download `ScoutTransfer.exe` from the [Releases](../../releases) page (or GitHub Actions artifacts)
2. Double-click to run — no installation needed
3. Windows Defender may show a warning on first launch — click "More info" → "Run anyway"

### Building from Source

```bash
# Install PyInstaller
pip install pyinstaller

# macOS (.app bundle)
pyinstaller --name ScoutTransfer --onedir --windowed --noconfirm \
  --add-data "scout_transfer.py:." --add-data "icons:icons" \
  --icon icons/mercs.png scout_transfer_gui.py

# Windows (.exe)
pyinstaller --name ScoutTransfer --onefile --windowed --noconfirm ^
  --add-data "scout_transfer.py;." --add-data "icons;icons" ^
  --icon icons/mercs.png scout_transfer_gui.py
```

Output will be in the `dist/` folder.

> **Tip:** A GitHub Actions workflow (`.github/workflows/build.yml`) is included that auto-builds both macOS and Windows versions when you push a git tag: `git tag v1.0 && git push --tags`

---

## Tablet Manager

The Tablet Manager tab in the GUI handles scouting app deployment to Android tablets via ADB.

### Prerequisites

- **ADB** must be installed and available in your system PATH
  - macOS: `brew install android-platform-tools`
  - Windows: Download from [Android SDK Platform Tools](https://developer.android.com/tools/releases/platform-tools)
- Tablets must have **USB debugging enabled** (Settings → Developer Options → USB Debugging)

### Workflow

1. **Start ADB Server** — Click the button to initialize the ADB connection
2. **Discover Devices** — Connected tablets appear with their serial numbers and current app versions
3. **Fetch Releases** — Pull the latest scouting app releases from GitHub (`Mercs-MSA/FRC_ScoutingDataCollection`)
4. **Download** — Download an APK with progress tracking and SHA1 checksum verification
5. **Install** — Select tablets and install the downloaded APK (auto-uninstalls old version first)
