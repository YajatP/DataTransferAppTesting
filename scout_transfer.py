#!/usr/bin/env python3
"""
FRC 6369 Scouting Data Transfer — Minimal Edition
Receives QR-scanned scouting data via serial → SQLite → CSV export.

Usage:
  python scout_transfer.py                        # serial mode (default)
  python scout_transfer.py --port /dev/cu.usbserial-1420  # specify port
  python scout_transfer.py --stdin                # paste/pipe mode (no scanner needed)
  python scout_transfer.py --export               # just export existing DB to CSV and quit

Controls:
  Ctrl+C  →  export all data to CSV and exit
"""

import argparse
import csv
import json
import os
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    import serial
    import serial.tools.list_ports
except ImportError:
    serial = None

# ─── ANSI Colors ───────────────────────────────────────────────────────────────
class C:
    """Terminal colors — degrades gracefully if redirected."""
    _ok = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()
    RESET   = "\033[0m"   if _ok else ""
    BOLD    = "\033[1m"    if _ok else ""
    DIM     = "\033[2m"    if _ok else ""
    GREEN   = "\033[92m"   if _ok else ""
    RED     = "\033[91m"   if _ok else ""
    YELLOW  = "\033[93m"   if _ok else ""
    CYAN    = "\033[96m"   if _ok else ""
    MAGENTA = "\033[95m"   if _ok else ""
    BLUE    = "\033[94m"   if _ok else ""
    BG_GREEN  = "\033[42m" if _ok else ""
    BG_RED    = "\033[41m" if _ok else ""
    BG_YELLOW = "\033[43m" if _ok else ""
    BG_BLUE   = "\033[44m" if _ok else ""

def ok(msg):    print(f"  {C.GREEN}✓{C.RESET} {msg}")
def warn(msg):  print(f"  {C.YELLOW}⚠{C.RESET} {C.YELLOW}{msg}{C.RESET}")
def err(msg):   print(f"  {C.RED}✗{C.RESET} {C.RED}{msg}{C.RESET}")
def info(msg):  print(f"  {C.CYAN}ℹ{C.RESET} {C.DIM}{msg}{C.RESET}")
def banner(msg, bg=C.BG_BLUE):
    print(f"\n{bg}{C.BOLD}  {msg}  {C.RESET}\n")

# ─── Field Definitions ────────────────────────────────────────────────────────
# Pulled directly from the existing constants.py — keeps QR data 100% compatible
DELIMITER = "||"

FIELDS = {
    "pit": {
        "form": "TEXT",
        "team": "INTEGER",
        "scouters": "TEXT",
        "weight": "INTEGER",
        "height": "INTEGER",
        "canShoot": "BOOLEAN",
        "climbFrontL1": "BOOLEAN",
        "climbFrontL2": "BOOLEAN",
        "climbFrontL3": "BOOLEAN",
        "climbSideL1": "BOOLEAN",
        "climbSideL2": "BOOLEAN",
        "climbSideL3": "BOOLEAN",
        "climbTime": "INTEGER",
        "groundIntake": "BOOLEAN",
        "turret": "BOOLEAN",
        "hood": "BOOLEAN",
        "drum": "BOOLEAN",
        "other": "BOOLEAN",
        "numShooters": "INTEGER",
        "shooter": "BOOLEAN",
        "defense": "BOOLEAN",
        "feed": "BOOLEAN",
        "hopperWidth": "INTEGER",
        "hopperLength": "INTEGER",
        "hopperHeight": "INTEGER",
        "hopperStorageEstimate": "INTEGER",
        "driverYears": "INTEGER",
        "operatorYears": "INTEGER",
        "coachYears": "INTEGER",
        "isCoachAdult": "BOOLEAN",
        "drivebase": "TEXT",
        "notes": "TEXT",
        "canAutoLeft": "BOOLEAN",
        "canAutoMid": "BOOLEAN",
        "canAutoRight": "BOOLEAN",
        "canDepot": "BOOLEAN",
        "canOutpost": "BOOLEAN",
        "canNeutral": "BOOLEAN",
        "canClimb": "BOOLEAN",
        "autonFuel": "INTEGER",
        "kitbotType": "TEXT",
        "isModifiedKit": "BOOLEAN",
    },
    "auton": {
        "form": "TEXT",
        "team": "INTEGER",
        "scouter": "TEXT",
        "match": "INTEGER",
        "alliance": "TEXT",
        "startPos": "TEXT",
        "autoLeave": "BOOLEAN",
        "depotDisrupted": "BOOLEAN",
        "outpostDisrupted": "BOOLEAN",
        "topDisrupted": "BOOLEAN",
        "middleDisrupted": "BOOLEAN",
        "bottomDisrupted": "BOOLEAN",
        "autoCycles": "INTEGER",
        "estimatedFuel": "INTEGER",
        "rightClimb": "BOOLEAN",
        "middleClimb": "BOOLEAN",
        "leftClimb": "BOOLEAN",
        "centerLineCrossed": "BOOLEAN",
        "overBumb": "BOOLEAN",
        "underTrench": "BOOLEAN",
    },
    "match": {
        "form": "TEXT",
        "team1": "INTEGER",
        "team2": "INTEGER",
        "team3": "INTEGER",
        "scouter": "TEXT",
        "alliance": "TEXT",
        "match": "INTEGER",

        "team1Shooter": "BOOLEAN",
        "team2Shooter": "BOOLEAN",
        "team3Shooter": "BOOLEAN",
        "team1Defender": "BOOLEAN",
        "team2Defender": "BOOLEAN",
        "team3Defender": "BOOLEAN",
        "team1Shunter": "BOOLEAN",
        "team2Shunter": "BOOLEAN",
        "team3Shunter": "BOOLEAN",
        
        "team1CollectionRate": "DOUBLE",
        "team2CollectionRate": "DOUBLE",
        "team3CollectionRate": "DOUBLE",

        "team1ShootingAccuracy": "DOUBLE",
        "team2ShootingAccuracy": "DOUBLE",
        "team3ShootingAccuracy": "DOUBLE",
        "team1ShootingRate": "DOUBLE",
        "team2ShootingRate": "DOUBLE",
        "team3ShootingRate": "DOUBLE",
        "team1Counterdefense": "BOOLEAN",
        "team2Counterdefense": "BOOLEAN",
        "team3Counterdefense": "BOOLEAN",
        "team1CyclesPerAllianceShift": "INTEGER",
        "team2CyclesPerAllianceShift": "INTEGER",
        "team3CyclesPerAllianceShift": "INTEGER",

        "team1ShunterRate": "DOUBLE",
        "team2ShunterRate": "DOUBLE",
        "team3ShunterRate": "DOUBLE",

        "team1DefenseIsEffective": "BOOLEAN",
        "team2DefenseIsEffective": "BOOLEAN",
        "team3DefenseIsEffective": "BOOLEAN",
        "team1DefendLocations": "TEXT",
        "team2DefendLocations": "TEXT",
        "team3DefendLocations": "TEXT",


        "team1EndgameLevel": "INTEGER",
        "team2EndgameLevel": "INTEGER",
        "team3EndgameLevel": "INTEGER",
        "team1ClimbPosition": "none",
        "team2ClimbPosition": "none",
        "team3ClimbPosition": "none",
        "team1ClimbedFromRack": "BOOLEAN",
        "team2ClimbedFromRack": "BOOLEAN",
        "team3ClimbedFromRack": "BOOLEAN",
        "team1ClimbSpeed": "INTEGER",
        "team2ClimbSpeed": "INTEGER",
        "team3ClimbSpeed": "INTEGER",

        "yellowCard": "BOOLEAN",
        "redCard": "BOOLEAN",
        "team1NoShow": "BOOLEAN",
        "team2NoShow": "BOOLEAN",
        "team3NoShow": "BOOLEAN",
        "team1Disabled": "BOOLEAN",
        "team2Disabled": "BOOLEAN",
        "team3Disabled": "BOOLEAN",
        "penalties": "BOOLEAN",
        "isMarkedForReview": "BOOLEAN",
        "comments": "TEXT",
    },
}

# ─── Type conversion (mirrors original utils.convert_types) ────────────────────
def convert_value(raw: str):
    """Convert a raw string value using json.loads — handles null, true/false, ints, floats."""
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return raw

# ─── Database ──────────────────────────────────────────────────────────────────
DB_FILE = "scouting.db"

def init_db(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    for form, fields in FIELDS.items():
        field_defs = ", ".join(
            f'"{name}" {ftype}' for name, ftype in fields.items()
        )
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {form} (
                rowid INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                {field_defs}
            )
        """)

        # ── Auto-migrate: add any new columns to existing tables ──
        cur.execute(f"PRAGMA table_info({form})")
        existing_cols = {row[1] for row in cur.fetchall()}  # row[1] = column name
        for col_name, col_type in fields.items():
            if col_name not in existing_cols:
                cur.execute(f'ALTER TABLE {form} ADD COLUMN "{col_name}" {col_type}')
                info(f"Migrated: added column '{col_name}' to '{form}' table")

    conn.commit()
    return conn

def is_duplicate(conn: sqlite3.Connection, form: str, row: dict) -> bool:
    """Check if an identical row already exists (ignoring rowid/timestamp)."""
    cur = conn.cursor()
    conditions = []
    values = []
    for k, v in row.items():
        if v is None:
            conditions.append(f'"{k}" IS NULL')
        else:
            conditions.append(f'"{k}" = ?')
            values.append(v)
    where = " AND ".join(conditions)
    cur.execute(f"SELECT 1 FROM {form} WHERE {where} LIMIT 1", values)
    return cur.fetchone() is not None

def insert_row(conn: sqlite3.Connection, form: str, row: dict) -> bool:
    """Insert a row. Returns True if inserted, False if duplicate."""
    if is_duplicate(conn, form, row):
        return False
    cur = conn.cursor()
    cols = ", ".join(f'"{k}"' for k in row.keys())
    placeholders = ", ".join("?" for _ in row)
    cur.execute(
        f"INSERT INTO {form} ({cols}) VALUES ({placeholders})",
        list(row.values()),
    )
    conn.commit()
    return True

def row_count(conn: sqlite3.Connection, form: str) -> int:
    return conn.execute(f"SELECT COUNT(*) FROM {form}").fetchone()[0]

# ─── Parse a scanned line ─────────────────────────────────────────────────────
def parse_scan(line: str) -> Tuple[Optional[str], Optional[dict], Optional[str]]:
    """
    Parse a QR-scanned line.
    Returns (form_name, data_dict, error_string).
    On error, form_name and data_dict will be None.
    """
    line = line.strip()
    if not line:
        return None, None, None  # blank line, silently skip

    parts = line.split(DELIMITER)
    form_name = parts[0].strip().lower()

    if form_name not in FIELDS:
        return None, None, f"Unknown form '{form_name}'"

    expected_fields = list(FIELDS[form_name].keys())
    if len(parts) != len(expected_fields):
        return None, None, (
            f"Field count mismatch for '{form_name}': "
            f"got {len(parts)}, expected {len(expected_fields)}"
        )

    row = {}
    for field_name, raw_value in zip(expected_fields, parts):
        row[field_name] = convert_value(raw_value.strip())

    return form_name, row, None

# ─── CSV Export ────────────────────────────────────────────────────────────────
def export_csv(conn: sqlite3.Connection, output_dir: str = "."):
    """Export each table to a CSV file. Returns list of (form, path, count)."""
    results = []
    for form in FIELDS:
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM {form}")
        rows = cur.fetchall()
        if not rows:
            results.append((form, None, 0))
            continue

        headers = [desc[0] for desc in cur.description]
        path = os.path.join(output_dir, f"{form}_export.csv")
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)
        results.append((form, path, len(rows)))
    return results

# ─── Status line ───────────────────────────────────────────────────────────────
class StatusLine:
    """Persistent bottom status bar that updates in-place."""
    def __init__(self):
        self.counts = {form: 0 for form in FIELDS}
        self.dupes = 0
        self.errors = 0
        self.last_scan = None

    def update(self, conn):
        for form in FIELDS:
            self.counts[form] = row_count(conn, form)

    def draw(self):
        parts = []
        for form, count in self.counts.items():
            parts.append(f"{C.BOLD}{form}{C.RESET}: {C.GREEN}{count}{C.RESET}")
        counts_str = "  │  ".join(parts)
        dupe_str = f"{C.YELLOW}{self.dupes} dupes{C.RESET}" if self.dupes else f"{C.DIM}0 dupes{C.RESET}"
        err_str = f"{C.RED}{self.errors} errors{C.RESET}" if self.errors else f"{C.DIM}0 errors{C.RESET}"
        last = self.last_scan or "waiting..."

        line = f"  {counts_str}  │  {dupe_str}  │  {err_str}  │  last: {C.DIM}{last}{C.RESET}"
        # Clear line and rewrite
        print(f"\r\033[K{line}", end="", flush=True)

# ─── Serial helpers ────────────────────────────────────────────────────────────
def list_serial_ports():
    if serial is None:
        return []
    return list(serial.tools.list_ports.comports())

def pick_serial_port(requested: Optional[str]) -> Optional[str]:
    """Find a valid serial port. Returns port string or None."""
    ports = list_serial_ports()
    if requested:
        for p in ports:
            if p.device == requested:
                return requested
        warn(f"Requested port '{requested}' not found")

    if not ports:
        return None

    if len(ports) == 1:
        return ports[0].device

    # Multiple ports — let user choose
    print(f"\n  {C.BOLD}Available serial ports:{C.RESET}")
    for i, p in enumerate(ports):
        print(f"    {C.CYAN}[{i+1}]{C.RESET} {p.device}  {C.DIM}({p.description}){C.RESET}")
    try:
        choice = input(f"\n  Select port [1-{len(ports)}]: ").strip()
        idx = int(choice) - 1
        if 0 <= idx < len(ports):
            return ports[idx].device
    except (ValueError, EOFError, KeyboardInterrupt):
        pass
    return None

# ─── Main loops ───────────────────────────────────────────────────────────────
def process_line(line: str, conn: sqlite3.Connection, status: StatusLine):
    """Process one scanned line. Prints feedback and updates status."""
    form, row, error = parse_scan(line)

    if form is None and error is None:
        return  # blank line
    if error:
        err(error)
        status.errors += 1
        print()  # newline before status redraws
        status.draw()
        return

    team = row.get("team", "?")
    inserted = insert_row(conn, form, row)

    if inserted:
        ok(f"{C.BOLD}{form.upper()}{C.RESET}  team {C.BOLD}{team}{C.RESET}  →  saved")
    else:
        warn(f"{form.upper()}  team {team}  →  duplicate, skipped")
        status.dupes += 1

    now = datetime.now().strftime("%H:%M:%S")
    status.last_scan = f"{form} #{team} @ {now}"
    status.update(conn)
    print()  # newline before status redraws
    status.draw()

def run_serial(conn: sqlite3.Connection, port: str, baud: int, status: StatusLine):
    """Main serial listening loop."""
    banner(f"LISTENING  ·  {port} @ {baud} baud", C.BG_BLUE)
    info("Scan QR codes now. Press Ctrl+C to export & quit.\n")
    status.draw()

    ser = serial.Serial(port, baud, timeout=1)
    buf = ""
    try:
        while True:
            if ser.in_waiting:
                chunk = ser.read(ser.in_waiting).decode("utf-8", errors="replace")
                buf += chunk
                while "\n" in buf:
                    line, buf = buf.split("\n", 1)
                    print()  # move past status line
                    process_line(line, conn, status)
            time.sleep(0.03)
    finally:
        ser.close()

def run_stdin(conn: sqlite3.Connection, status: StatusLine):
    """Interactive paste/pipe mode — reads lines from stdin."""
    banner("STDIN MODE  ·  paste or pipe QR data lines", C.BG_BLUE)
    info("Type/paste scanned lines, one per line. Ctrl+C or Ctrl+D to export & quit.\n")
    status.draw()

    try:
        while True:
            try:
                print()  # move past status line
                line = input(f"  {C.DIM}scan>{C.RESET} ")
                process_line(line, conn, status)
            except EOFError:
                break
    except KeyboardInterrupt:
        pass

# ─── Entry ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="FRC 6369 Scouting Data Transfer — Minimal Edition"
    )
    parser.add_argument("--port", help="Serial port (e.g. /dev/cu.usbserial-1420 or COM3)")
    parser.add_argument("--baud", type=int, default=115200, help="Baud rate (default: 115200)")
    parser.add_argument("--db", default=DB_FILE, help=f"SQLite database file (default: {DB_FILE})")
    parser.add_argument("--stdin", action="store_true", help="Read from stdin instead of serial")
    parser.add_argument("--export", action="store_true", help="Export existing DB to CSV and quit")
    args = parser.parse_args()

    # ── Startup banner ──
    print()
    banner("FRC 6369  ·  SCOUTING DATA TRANSFER", C.BG_BLUE)
    info(f"Database: {C.BOLD}{Path(args.db).absolute()}{C.RESET}")

    # ── Init DB ──
    conn = init_db(args.db)
    status = StatusLine()
    status.update(conn)

    existing_pit = row_count(conn, "pit")
    existing_match = row_count(conn, "match")
    if existing_pit or existing_match:
        info(f"Existing data: {C.GREEN}{existing_pit}{C.RESET} pit, {C.GREEN}{existing_match}{C.RESET} match rows")

    # ── Export-only mode ──
    if args.export:
        do_export(conn)
        conn.close()
        return

    # ── Choose input mode ──
    try:
        if args.stdin:
            run_stdin(conn, status)
        else:
            if serial is None:
                err("pyserial not installed. Run: pip install pyserial")
                err("Or use --stdin mode to paste data manually.\n")
                conn.close()
                sys.exit(1)

            port = pick_serial_port(args.port)
            if not port:
                err("No serial ports found.")
                warn("Falling back to --stdin mode.\n")
                run_stdin(conn, status)
            else:
                run_serial(conn, port, args.baud, status)
    except KeyboardInterrupt:
        pass

    # ── Export on exit ──
    print("\n")
    do_export(conn)
    conn.close()

def do_export(conn: sqlite3.Connection):
    """Export all tables and print a summary."""
    banner("EXPORTING TO CSV", C.BG_GREEN)
    results = export_csv(conn)

    any_data = False
    for form, path, count in results:
        if count > 0:
            any_data = True
            ok(f"{form.upper():>5}  →  {C.BOLD}{count}{C.RESET} rows  →  {C.CYAN}{path}{C.RESET}")
        else:
            info(f"{form.upper():>5}  →  {C.DIM}empty, skipped{C.RESET}")

    if not any_data:
        warn("No data to export.\n")
    else:
        print()
        banner("DONE ✓", C.BG_GREEN)

if __name__ == "__main__":
    main()
