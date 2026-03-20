#!/usr/bin/env python3
"""
FRC 6369 Scouting Data Transfer — GUI Edition
A clean, dark-themed PySide6 desktop app wrapping scout_transfer.py.
"""

import sys
import os
import time
import hashlib
import shutil
import subprocess
import ssl
import urllib.request
import zipfile
import stat
import platform
import concurrent.futures
from datetime import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    requests = None

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QLineEdit,
    QTextEdit,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QFileDialog,
    QMessageBox,
    QFrame,
    QSplitter,
    QGroupBox,
    QSpinBox,
    QSizePolicy,
    QProgressBar,
    QListWidget,
    QListWidgetItem,
    QScrollArea,
    QMenu,
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QSize
from PySide6.QtGui import QFont, QColor, QIcon

# Import core logic from scout_transfer.py (same directory)
import scout_transfer as core

# ─── Constants ─────────────────────────────────────────────────────────────────
GITHUB_REPO = "Mercs-MSA/FRC_ScoutingDataCollection"
COLLECTION_APP_ID = "com.mercs.scouting"

# ─── Theme Colors ──────────────────────────────────────────────────────────────
COLORS = {
    "bg":          "#0A0A0A",
    "sidebar":     "#0E0E0E",
    "surface":     "#131315",
    "surface2":    "#1A1A1D",
    "border":      "#222225",
    "border_lt":   "#2E2E32",
    "text":        "#E8E8E8",
    "text_dim":    "#707075",
    "text_muted":  "#454548",
    "red":         "#D32F2F",     # Softer Crimson Red
    "red_hover":   "#B71C1C",     # Darker hover state
    "red_bg":      "#2B1216",     # Subtle red tint for backgrounds
    "green":       "#34C759",
    "green_bg":    "#0C1A10",
    "yellow":      "#FFB800",
    "yellow_bg":   "#1A1508",
    "blue":        "#4A9EFF",
}

STYLESHEET = f"""
QMainWindow {{
    background-color: {COLORS['bg']};
}}
QWidget#centralwidget {{
    background-color: {COLORS['bg']};
}}
QWidget {{
    color: {COLORS['text']};
    font-family: 'Menlo', 'Consolas', 'SF Mono', 'Courier New', monospace;
    font-size: 12px;
}}
QGroupBox {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    margin-top: 16px;
    padding: 16px 10px 10px 10px;
    font-weight: 700;
    font-size: 10px;
    color: {COLORS['text_dim']};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 2px 8px;
    color: {COLORS['red']};
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 2px;
}}
QPushButton {{
    background-color: {COLORS['surface2']};
    border: 1px solid {COLORS['border']};
    border-radius: 3px;
    padding: 8px 16px;
    color: {COLORS['text']};
    font-weight: 600;
    font-size: 11px;
    min-height: 16px;
    letter-spacing: 0.5px;
}}
QPushButton:hover {{
    background-color: {COLORS['border']};
    border-color: {COLORS['border_lt']};
}}
QPushButton:pressed {{
    background-color: {COLORS['surface']};
}}
QPushButton:disabled {{
    color: {COLORS['text_muted']};
    border-color: {COLORS['border']};
}}
QPushButton#primaryBtn {{
    background-color: {COLORS['red']};
    border: none;
    color: #FFFFFF;
    font-weight: 700;
    padding: 10px 24px;
}}
QPushButton#primaryBtn:hover {{
    background-color: {COLORS['red_hover']};
}}
QPushButton#primaryBtn:pressed {{
    background-color: #A01830;
}}
QPushButton#connectBtn {{
    background-color: {COLORS['green_bg']};
    border-color: #1A3A20;
    color: {COLORS['green']};
}}
QPushButton#connectBtn:hover {{
    background-color: #0F2A15;
    border-color: {COLORS['green']};
}}
QPushButton#disconnectBtn {{
    background-color: {COLORS['red_bg']};
    border-color: #2A1018;
    color: {COLORS['red']};
}}
QPushButton#disconnectBtn:hover {{
    background-color: #200A10;
    border-color: {COLORS['red']};
}}
QPushButton#exportBtn {{
    background-color: {COLORS['red']};
    border: none;
    color: #FFFFFF;
    font-weight: 700;
    padding: 10px 24px;
}}
QPushButton#exportBtn:hover {{
    background-color: {COLORS['red_hover']};
}}
QPushButton#clearBtn {{
    background-color: {COLORS['red_bg']};
    border-color: #2A1018;
    color: {COLORS['red']};
}}
QPushButton#clearBtn:hover {{
    border-color: {COLORS['red']};
}}
QComboBox {{
    background-color: {COLORS['surface2']};
    border: 1px solid {COLORS['border']};
    border-radius: 3px;
    padding: 6px 12px;
    color: {COLORS['text']};
    min-width: 140px;
    font-size: 11px;
}}
QComboBox::drop-down {{
    border: none;
    padding-right: 8px;
}}
QComboBox QAbstractItemView {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    color: {COLORS['text']};
    selection-background-color: {COLORS['red_bg']};
    selection-color: {COLORS['red']};
}}
QLineEdit {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 3px;
    padding: 8px 12px;
    color: {COLORS['text']};
    font-family: 'Menlo', 'Consolas', 'SF Mono', monospace;
    font-size: 12px;
}}
QLineEdit:focus {{
    border-color: {COLORS['red']};
}}
QTextEdit {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 3px;
    padding: 8px;
    color: {COLORS['text']};
    font-family: 'Menlo', 'Consolas', 'SF Mono', monospace;
    font-size: 11px;
}}
QTabWidget::pane {{
    background-color: {COLORS['bg']};
    border: none;
    top: 0px;
}}
QTabBar::tab {{
    background-color: transparent;
    border: none;
    border-bottom: 2px solid transparent;
    padding: 10px 24px;
    color: {COLORS['text_dim']};
    font-weight: 600;
    font-size: 11px;
    letter-spacing: 1px;
    margin-right: 0px;
}}
QTabBar::tab:selected {{
    color: {COLORS['red']};
    border-bottom: 2px solid {COLORS['red']};
}}
QTabBar::tab:hover:!selected {{
    color: {COLORS['text']};
    border-bottom: 2px solid {COLORS['border_lt']};
}}
QTableWidget {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 3px;
    gridline-color: {COLORS['border']};
    color: {COLORS['text']};
    font-size: 11px;
}}
QTableWidget::item {{
    padding: 5px 8px;
    border-bottom: 1px solid {COLORS['border']};
}}
QTableWidget::item:selected {{
    background-color: {COLORS['red_bg']};
    color: {COLORS['red']};
}}
QHeaderView::section {{
    background-color: {COLORS['surface2']};
    color: {COLORS['text_dim']};
    border: none;
    border-bottom: 1px solid {COLORS['border']};
    border-right: 1px solid {COLORS['border']};
    padding: 7px 8px;
    font-weight: 700;
    font-size: 10px;
    letter-spacing: 1px;
}}
QScrollBar:vertical {{
    background-color: {COLORS['bg']};
    width: 6px;
    border: none;
}}
QScrollBar::handle:vertical {{
    background-color: {COLORS['border_lt']};
    border-radius: 3px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background-color: {COLORS['text_muted']};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QScrollBar:horizontal {{
    background-color: {COLORS['bg']};
    height: 6px;
    border: none;
}}
QScrollBar::handle:horizontal {{
    background-color: {COLORS['border_lt']};
    border-radius: 3px;
    min-width: 30px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}
QSpinBox {{
    background-color: {COLORS['surface2']};
    border: 1px solid {COLORS['border']};
    border-radius: 3px;
    padding: 6px 12px;
    color: {COLORS['text']};
}}
QProgressBar {{
    background-color: {COLORS['surface2']};
    border: 1px solid {COLORS['border']};
    border-radius: 3px;
    height: 6px;
    text-align: center;
    font-size: 10px;
    color: {COLORS['text_dim']};
}}
QProgressBar::chunk {{
    background-color: {COLORS['red']};
    border-radius: 2px;
}}
QListWidget {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 3px;
    color: {COLORS['text']};
    font-size: 11px;
    padding: 4px;
}}
QListWidget::item {{
    padding: 8px 10px;
    border-bottom: 1px solid {COLORS['border']};
    border-radius: 2px;
    margin: 1px 0;
}}
QListWidget::item:selected {{
    background-color: {COLORS['red_bg']};
    color: {COLORS['red']};
}}
QListWidget::item:hover:!selected {{
    background-color: {COLORS['surface2']};
}}
"""


# ─── Status Dot Widget ─────────────────────────────────────────────────────────
class StatusDot(QWidget):
    """A colored dot with a label — used for status indicators."""

    def __init__(self, label: str, color: str = COLORS["text_dim"], parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 12, 0)
        layout.setSpacing(6)

        self.dot = QLabel("●")
        self.dot.setFixedWidth(16)
        self.dot.setAlignment(Qt.AlignCenter)
        self.dot.setStyleSheet(f"color: {color}; font-size: 10px;")

        self.label = QLabel(label)
        self.label.setStyleSheet(f"color: {COLORS['text']}; font-size: 12px;")

        layout.addWidget(self.dot)
        layout.addWidget(self.label)

    def set_status(self, text: str, color: str):
        self.dot.setStyleSheet(f"color: {color}; font-size: 10px;")
        self.label.setText(text)


# ─── Serial Reader Thread ─────────────────────────────────────────────────────
class SerialReaderThread(QThread):
    """Background thread that reads lines from a serial port."""
    line_received = Signal(str)
    error_occurred = Signal(str)
    disconnected = Signal()

    def __init__(self, port: str, baud: int):
        super().__init__()
        self.port = port
        self.baud = baud
        self._running = True

    def run(self):
        try:
            import serial as _serial
            ser = _serial.Serial(self.port, self.baud, timeout=0.5)
            buf = ""
            while self._running:
                if ser.in_waiting:
                    chunk = ser.read(ser.in_waiting).decode("utf-8", errors="replace")
                    buf += chunk
                    while "\n" in buf:
                        line, buf = buf.split("\n", 1)
                        line = line.strip()
                        if line:
                            self.line_received.emit(line)
                time.sleep(0.03)
            ser.close()
        except Exception as e:
            self.error_occurred.emit(str(e))
        finally:
            self.disconnected.emit()

    def stop(self):
        self._running = False


# ─── ADB Downloader / Resolver ────────────────────────────────────────────────
ADB_BIN_CACHE = None

def get_adb_path(log_callback=None) -> str:
    """Resolve ADB path. Triggers an automatic download if completely missing."""
    global ADB_BIN_CACHE
    if ADB_BIN_CACHE: return ADB_BIN_CACHE

    sys_adb = shutil.which("adb")
    if sys_adb:
        ADB_BIN_CACHE = sys_adb
        return sys_adb

    from platformdirs import user_data_dir
    app_dir = Path(user_data_dir("scouting_transfer", "mercs", ensure_exists=True))
    os_name = platform.system().lower()
    
    adb_exe = "adb.exe" if os_name == "windows" else "adb"
    local_adb = app_dir / "platform-tools" / adb_exe
    
    if local_adb.exists():
        ADB_BIN_CACHE = str(local_adb)
        return ADB_BIN_CACHE

    if log_callback:
        log_callback("ADB not found. Downloading Android Platform Tools (~6MB)...")
        
    if os_name == "windows":
        url = "https://dl.google.com/android/repository/platform-tools-latest-windows.zip"
    elif os_name == "darwin":
        url = "https://dl.google.com/android/repository/platform-tools-latest-darwin.zip"
    else:
        url = "https://dl.google.com/android/repository/platform-tools-latest-linux.zip"
        
    zip_path = app_dir / "platform-tools.zip"
    
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        with urllib.request.urlopen(url, context=ctx) as response, open(zip_path, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
            
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(app_dir)
            
        zip_path.unlink()
        
        if os_name != "windows":
            st = os.stat(local_adb)
            os.chmod(local_adb, st.st_mode | stat.S_IEXEC)
            
        if log_callback:
            log_callback("ADB downloaded and installed successfully.")
            
        ADB_BIN_CACHE = str(local_adb)
        return ADB_BIN_CACHE
        
    except Exception as e:
        if log_callback:
            log_callback(f"Failed to auto-download ADB: {e}")
        return "adb"  # Blind fallback


# ─── ADB / Tablet Manager Workers ─────────────────────────────────────────────
class AdbStartWorker(QThread):
    """Start ADB server and create a connection."""
    log = Signal(str)
    finished = Signal(bool)
    error = Signal(str)

    def run(self):
        try:
            adb_exe = get_adb_path(lambda msg: self.log.emit(msg))
            result = subprocess.run(
                [adb_exe, "start-server"], capture_output=True, text=True, timeout=15
            )
            if result.returncode != 0:
                self.error.emit(f"ADB start-server failed: {result.stderr.strip()}")
                self.finished.emit(False)
            else:
                self.finished.emit(True)
        except Exception as e:
            self.error.emit(str(e))
            self.finished.emit(False)


class AdbDeviceWorker(QThread):
    """List connected ADB devices with scouting app version."""
    finished = Signal(list)  # list of dicts
    error = Signal(str)

    def run(self):
        try:
            adb_exe = get_adb_path()
            result = subprocess.run(
                [adb_exe, "devices", "-l"], capture_output=True, text=True, timeout=10
            )
            devices = []
            for line in result.stdout.strip().split("\n")[1:]:
                parts = line.split()
                if len(parts) >= 2 and parts[1] == "device":
                    serial = parts[0]
                    # Get app version
                    ver_result = subprocess.run(
                        [adb_exe, "-s", serial, "shell", "dumpsys", "package",
                         COLLECTION_APP_ID, "|", "grep", "versionName"],
                        capture_output=True, text=True, timeout=10
                    )
                    version = "not installed"
                    for vline in ver_result.stdout.split("\n"):
                        if "versionName" in vline:
                            version = vline.strip().split("=", 1)[-1]
                            break
                    # Get device model
                    model = "unknown"
                    for p in parts[2:]:
                        if p.startswith("model:"):
                            model = p.split(":", 1)[1]
                    devices.append({"serial": serial, "model": model, "app_version": version})
            self.finished.emit(devices)
        except FileNotFoundError:
            self.error.emit("ADB not found in PATH.")
            self.finished.emit([])
        except Exception as e:
            self.error.emit(str(e))
            self.finished.emit([])


class FetchReleasesWorker(QThread):
    """Fetch APK releases from GitHub."""
    finished = Signal(list)
    error = Signal(str)

    def run(self):
        if requests is None:
            self.error.emit("'requests' library not installed.")
            self.finished.emit([])
            return
        try:
            url = f"https://api.github.com/repos/{GITHUB_REPO}/releases"
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            releases = []
            for rel in resp.json():
                apk_url = sha1_url = None
                for asset in rel.get("assets", []):
                    if asset["name"].endswith(".apk"):
                        apk_url = asset["browser_download_url"]
                    elif asset["name"].endswith(".sha1"):
                        sha1_url = asset["browser_download_url"]
                if apk_url:
                    releases.append({
                        "tag": rel["tag_name"],
                        "title": rel.get("name") or rel["tag_name"],
                        "prerelease": rel.get("prerelease", False),
                        "apk_url": apk_url,
                        "sha1_url": sha1_url,
                    })
            self.finished.emit(releases)
        except Exception as e:
            self.error.emit(str(e))
            self.finished.emit([])


class DownloadApkWorker(QThread):
    """Download an APK file with progress."""
    progress = Signal(int)
    finished = Signal(bool, str)  # success, path
    error = Signal(str)

    def __init__(self, url: str, dest_path: str):
        super().__init__()
        self.url = url
        self.dest_path = dest_path

    def run(self):
        try:
            resp = requests.get(self.url, stream=True, timeout=30)
            total = int(resp.headers.get("content-length", 0))
            downloaded = 0
            os.makedirs(os.path.dirname(self.dest_path), exist_ok=True)
            with open(self.dest_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total > 0:
                            self.progress.emit(int(100 * downloaded / total))
            self.finished.emit(True, self.dest_path)
        except Exception as e:
            self.error.emit(str(e))
            self.finished.emit(False, "")


class InstallApkWorker(QThread):
    """Install APK on selected devices via ADB."""
    log = Signal(str)
    finished = Signal(bool)

    def __init__(self, serials: list, apk_path: str):
        super().__init__()
        self.serials = serials
        self.apk_path = apk_path

    def run(self):
        try:
            adb_exe = get_adb_path()
            all_ok = True
            
            def install_to_device(serial):
                try:
                    self.log.emit(f"[{serial}] Starting installation...")
                    check = subprocess.run(
                        [adb_exe, "-s", serial, "shell", "pm", "list", "packages", COLLECTION_APP_ID],
                        capture_output=True, text=True, timeout=10
                    )
                    if COLLECTION_APP_ID in check.stdout:
                        self.log.emit(f"[{serial}] Uninstalling old version...")
                        subprocess.run(
                            [adb_exe, "-s", serial, "uninstall", COLLECTION_APP_ID],
                            capture_output=True, text=True, timeout=30
                        )
                    self.log.emit(f"[{serial}] Pushing new APK...")
                    result = subprocess.run(
                        [adb_exe, "-s", serial, "install", "-r", self.apk_path],
                        capture_output=True, text=True, timeout=120
                    )
                    if result.returncode == 0 and "Success" in result.stdout:
                        self.log.emit(f"[{serial}] ✓ Successfully installed")
                        return True
                    else:
                        self.log.emit(f"[{serial}] ✗ Failed: {result.stderr.strip()}")
                        return False
                except Exception as e:
                    self.log.emit(f"[{serial}] ✗ Error: {e}")
                    return False

            with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, len(self.serials))) as executor:
                futures = {executor.submit(install_to_device, s): s for s in self.serials}
                for future in concurrent.futures.as_completed(futures):
                    if not future.result():
                        all_ok = False
                        
            self.finished.emit(all_ok)
        except Exception as e:
            self.log.emit(f"Failed to find ADB: {e}")
            self.finished.emit(False)


# ─── Tablet Manager Widget ─────────────────────────────────────────────────────
class TabletManagerWidget(QWidget):
    """Full tablet management panel — ADB, releases, downloads, install."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.releases_data = []
        self.download_workers = {}
        from platformdirs import user_data_dir
        self.app_dir = user_data_dir("scouting_transfer", "mercs", ensure_exists=True)

        self._build_ui()
        self._refresh_downloaded()

    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 8, 0, 0)
        root.setSpacing(12)

        # ── Left: ADB & Devices ──
        left = QVBoxLayout()
        left.setSpacing(8)

        # ADB Status
        adb_group = QGroupBox("ADB CONNECTION")
        adb_layout = QVBoxLayout(adb_group)
        adb_layout.setSpacing(8)

        self.adb_status = StatusDot("ADB: Not Started", COLORS["text_dim"])
        adb_layout.addWidget(self.adb_status)

        adb_btns = QHBoxLayout()
        self.adb_start_btn = QPushButton("Start ADB Server")
        self.adb_start_btn.setObjectName("connectBtn")
        self.adb_start_btn.clicked.connect(self._start_adb)
        adb_btns.addWidget(self.adb_start_btn)
        adb_layout.addLayout(adb_btns)

        left.addWidget(adb_group)

        # Devices
        dev_group = QGroupBox("CONNECTED TABLETS")
        dev_layout = QVBoxLayout(dev_group)
        dev_layout.setSpacing(6)

        self.device_status = StatusDot("Devices: —", COLORS["text_dim"])
        dev_layout.addWidget(self.device_status)

        self.device_list = QListWidget()
        self.device_list.setSelectionMode(QListWidget.MultiSelection)
        self.device_list.setMinimumHeight(120)
        dev_layout.addWidget(self.device_list)

        dev_btns = QHBoxLayout()
        self.refresh_dev_btn = QPushButton("Refresh Devices")
        self.refresh_dev_btn.clicked.connect(self._refresh_devices)
        dev_btns.addWidget(self.refresh_dev_btn)
        dev_layout.addLayout(dev_btns)

        left.addWidget(dev_group, stretch=1)

        # Install button
        self.install_btn = QPushButton("Install to Selected Tablets")
        self.install_btn.setObjectName("exportBtn")
        self.install_btn.setMinimumHeight(42)
        self.install_btn.clicked.connect(self._install_to_devices)
        left.addWidget(self.install_btn)

        # Install log
        self.install_log = QTextEdit()
        self.install_log.setReadOnly(True)
        self.install_log.setMaximumHeight(120)
        self.install_log.setStyleSheet(
            f"background-color: {COLORS['bg']}; border: 1px solid {COLORS['border']}; "
            f"border-radius: 6px; font-size: 11px;"
        )
        self.install_log.setPlaceholderText("Install log will appear here...")
        left.addWidget(self.install_log)

        left_widget = QWidget()
        left_widget.setLayout(left)
        left_widget.setMaximumWidth(380)

        root.addWidget(left_widget)

        # ── Right: Releases ──
        right = QVBoxLayout()
        right.setSpacing(8)

        fetch_bar = QHBoxLayout()
        self.fetch_btn = QPushButton("Fetch Releases from GitHub")
        self.fetch_btn.setObjectName("exportBtn")
        self.fetch_btn.clicked.connect(self._fetch_releases)
        fetch_bar.addWidget(self.fetch_btn)

        self.fetch_status = QLabel("")
        self.fetch_status.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px;")
        fetch_bar.addWidget(self.fetch_status)
        fetch_bar.addStretch()
        right.addLayout(fetch_bar)

        # Available releases
        avail_group = QGroupBox("AVAILABLE RELEASES")
        avail_layout = QVBoxLayout(avail_group)

        self.avail_scroll = QScrollArea()
        self.avail_scroll.setWidgetResizable(True)
        self.avail_scroll.setStyleSheet(
            f"QScrollArea {{ border: none; background-color: {COLORS['surface']}; }}"
        )
        self.avail_container = QWidget()
        self.avail_items_layout = QVBoxLayout(self.avail_container)
        self.avail_items_layout.setSpacing(6)
        self.avail_items_layout.setAlignment(Qt.AlignTop)
        self.avail_scroll.setWidget(self.avail_container)
        avail_layout.addWidget(self.avail_scroll)

        right.addWidget(avail_group, stretch=1)

        # Downloaded releases
        dl_group = QGroupBox("DOWNLOADED RELEASES")
        dl_layout = QVBoxLayout(dl_group)

        self.dl_scroll = QScrollArea()
        self.dl_scroll.setWidgetResizable(True)
        self.dl_scroll.setStyleSheet(
            f"QScrollArea {{ border: none; background-color: {COLORS['surface']}; }}"
        )
        self.dl_container = QWidget()
        self.dl_items_layout = QVBoxLayout(self.dl_container)
        self.dl_items_layout.setSpacing(6)
        self.dl_items_layout.setAlignment(Qt.AlignTop)
        self.dl_scroll.setWidget(self.dl_container)
        dl_layout.addWidget(self.dl_scroll)

        right.addWidget(dl_group, stretch=1)

        root.addLayout(right, stretch=1)

    # ── ADB Actions ──
    def _start_adb(self):
        self.adb_status.set_status("ADB: Starting...", COLORS["yellow"])
        self.adb_start_btn.setEnabled(False)
        self._worker_adb = AdbStartWorker()
        self._worker_adb.finished.connect(self._on_adb_started)
        self._worker_adb.error.connect(self._on_adb_error)
        self._worker_adb.start()

    def _on_adb_started(self, success):
        self.adb_start_btn.setEnabled(True)
        if success:
            self.adb_status.set_status("ADB: Running", COLORS["green"])
            self._refresh_devices()
        else:
            self.adb_status.set_status("ADB: Failed", COLORS["red"])

    def _on_adb_error(self, msg):
        self.adb_status.set_status("ADB: Error", COLORS["red"])
        QMessageBox.warning(self, "ADB Error", msg)

    # ── Device Actions ──
    def _refresh_devices(self):
        self.device_status.set_status("Devices: Scanning...", COLORS["yellow"])
        self.device_list.clear()
        self._worker_dev = AdbDeviceWorker()
        self._worker_dev.finished.connect(self._on_devices_found)
        self._worker_dev.error.connect(lambda e: self.device_status.set_status(
            f"Devices: Error", COLORS["red"]
        ))
        self._worker_dev.start()

    def _on_devices_found(self, devices):
        self.device_list.clear()
        self._devices = devices
        if devices:
            self.device_status.set_status(
                f"Devices: {len(devices)} found", COLORS["green"]
            )
            for dev in devices:
                item = QListWidgetItem(
                    f"{dev['serial']}  ·  {dev['model']}  ·  App: {dev['app_version']}"
                )
                item.setData(Qt.UserRole, dev["serial"])
                self.device_list.addItem(item)
        else:
            self.device_status.set_status("Devices: None found", COLORS["text_dim"])

    # ── Release Actions ──
    def _fetch_releases(self):
        self.fetch_btn.setEnabled(False)
        self.fetch_status.setText("Fetching...")
        self._worker_fetch = FetchReleasesWorker()
        self._worker_fetch.finished.connect(self._on_releases_fetched)
        self._worker_fetch.error.connect(self._on_fetch_error)
        self._worker_fetch.start()

    def _on_fetch_error(self, msg):
        self.fetch_btn.setEnabled(True)
        self.fetch_status.setText(f"Error: {msg[:60]}")

    def _on_releases_fetched(self, releases):
        self.fetch_btn.setEnabled(True)
        self.releases_data = releases
        self.fetch_status.setText(f"{len(releases)} releases found")

        # Clear existing
        while self.avail_items_layout.count():
            child = self.avail_items_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for rel in releases:
            card = self._make_release_card(rel, downloaded=False)
            self.avail_items_layout.addWidget(card)

    def _make_release_card(self, rel, downloaded):
        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background-color: {COLORS['surface2']}; "
            f"border: 1px solid {COLORS['border']}; border-radius: 6px; "
            f"padding: 8px; }}"
        )
        layout = QVBoxLayout(card)
        layout.setSpacing(4)
        layout.setContentsMargins(10, 8, 10, 8)

        # Title row
        top = QHBoxLayout()
        title = QLabel(rel.get('title', rel.get('tag', '?')))
        title.setStyleSheet(f"color: {COLORS['text']}; font-weight: 600; font-size: 13px; border: none;")
        top.addWidget(title)

        tag_label = QLabel(rel.get('tag', ''))
        tag_label.setStyleSheet(
            f"background-color: #2a3a2a; color: {COLORS['green']}; "
            f"padding: 2px 8px; border-radius: 4px; font-size: 11px;"
        )
        top.addWidget(tag_label)

        if rel.get('prerelease'):
            pre_label = QLabel("pre-release")
            pre_label.setStyleSheet(
                f"background-color: #3a3a1a; color: {COLORS['yellow']}; "
                f"padding: 2px 8px; border-radius: 4px; font-size: 11px;"
            )
            top.addWidget(pre_label)

        top.addStretch()
        layout.addLayout(top)

        if not downloaded:
            # Download button + progress
            dl_row = QHBoxLayout()
            dl_btn = QPushButton("Download")
            dl_btn.setObjectName("connectBtn")
            progress = QProgressBar()
            progress.setVisible(False)
            progress.setFixedHeight(14)
            dl_btn.clicked.connect(lambda: self._download_release(rel, dl_btn, progress))
            dl_row.addWidget(dl_btn)
            dl_row.addWidget(progress, stretch=1)
            layout.addLayout(dl_row)
        else:
            # Action buttons for downloaded releases
            btn_row = QHBoxLayout()

            select_btn = QPushButton("Select for Install")
            select_btn.clicked.connect(lambda: self._select_apk(rel['tag']))
            btn_row.addWidget(select_btn)

            folder_btn = QPushButton("Open Folder")
            folder_btn.setFixedWidth(36)
            folder_btn.setToolTip("Open in Finder")
            folder_btn.clicked.connect(
                lambda: subprocess.run(["open", os.path.join(self.app_dir, rel['tag'])])
                if sys.platform == "darwin"
                else subprocess.run(["explorer", os.path.join(self.app_dir, rel['tag'])])
            )
            btn_row.addWidget(folder_btn)

            del_btn = QPushButton("Delete")
            del_btn.setFixedWidth(36)
            del_btn.setToolTip("Delete this version")
            del_btn.setObjectName("clearBtn")
            del_btn.clicked.connect(lambda checked=False, t=rel['tag']: self._delete_version(t))
            btn_row.addWidget(del_btn)

            btn_row.addStretch()
            layout.addLayout(btn_row)

        return card

    def _download_release(self, rel, btn, progress):
        tag = rel['tag']
        apk_url = rel['apk_url']
        sha1_url = rel.get('sha1_url')
        dest = os.path.join(self.app_dir, tag, "app-release.apk")

        btn.setEnabled(False)
        btn.setText("Downloading...")
        progress.setVisible(True)
        progress.setValue(0)

        # Download APK
        worker = DownloadApkWorker(apk_url, dest)
        worker.progress.connect(progress.setValue)
        worker.finished.connect(lambda ok, path: self._on_download_done(ok, path, tag, sha1_url, btn, progress))
        worker.error.connect(lambda e: self._on_download_error(e, btn, progress))
        self.download_workers[tag] = worker
        worker.start()

    def _on_download_done(self, success, path, tag, sha1_url, btn, progress):
        progress.setVisible(False)
        btn.setEnabled(True)
        if not success:
            btn.setText("Download (failed)")
            return

        btn.setText("Downloaded")

        # Download and verify SHA1 if available
        if sha1_url:
            try:
                sha1_dest = path + ".sha1"
                resp = requests.get(sha1_url, timeout=10)
                with open(sha1_dest, "wb") as f:
                    f.write(resp.content)
                # Verify
                expected = open(sha1_dest, "r").read().strip()
                sha1 = hashlib.sha1()
                with open(path, "rb") as f:
                    while chunk := f.read(8192):
                        sha1.update(chunk)
                if sha1.hexdigest() != expected:
                    QMessageBox.warning(self, "Checksum Failed",
                                        f"SHA1 mismatch for {tag}. The download may be corrupted.")
            except Exception:
                pass  # Non-critical

        self._refresh_downloaded()
        self.download_workers.pop(tag, None)

    def _on_download_error(self, error, btn, progress):
        progress.setVisible(False)
        btn.setEnabled(True)
        btn.setText("Download (error)")
        QMessageBox.warning(self, "Download Error", error)

    def _refresh_downloaded(self):
        # Clear existing
        while self.dl_items_layout.count():
            child = self.dl_items_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not os.path.isdir(self.app_dir):
            return

        for tag in sorted(os.listdir(self.app_dir), reverse=True):
            tag_dir = os.path.join(self.app_dir, tag)
            apk_path = os.path.join(tag_dir, "app-release.apk")
            if os.path.isdir(tag_dir) and os.path.isfile(apk_path):
                card = self._make_release_card({"tag": tag, "title": tag}, downloaded=True)
                self.dl_items_layout.addWidget(card)

    def _select_apk(self, tag):
        self._selected_apk_tag = tag
        QMessageBox.information(self, "Selected",
                                f"Version {tag} selected for installation.\n"
                                f"Select tablets on the left and click 'Install'.")

    def _delete_version(self, tag):
        reply = QMessageBox.warning(
            self, "Delete Version",
            f"Delete downloaded version {tag}?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                shutil.rmtree(os.path.join(self.app_dir, tag))
                self._refresh_downloaded()
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))

    # ── Install ──
    def _install_to_devices(self):
        selected = self.device_list.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Devices", "Select at least one tablet to install to.")
            return

        tag = getattr(self, '_selected_apk_tag', None)
        if not tag:
            # Try to pick the first downloaded version
            for t in sorted(os.listdir(self.app_dir), reverse=True):
                apk = os.path.join(self.app_dir, t, "app-release.apk")
                if os.path.isfile(apk):
                    tag = t
                    break
        if not tag:
            QMessageBox.warning(self, "No APK", "Download an APK first, then select it for install.")
            return

        apk_path = os.path.join(self.app_dir, tag, "app-release.apk")
        if not os.path.isfile(apk_path):
            QMessageBox.warning(self, "Missing APK", f"APK file not found for {tag}.")
            return

        serials = [item.data(Qt.UserRole) for item in selected]
        self.install_log.clear()
        self.install_log.append(f"Installing {tag} to {len(serials)} device(s)...\n")
        self.install_btn.setEnabled(False)

        self._worker_install = InstallApkWorker(serials, apk_path)
        self._worker_install.log.connect(self.install_log.append)
        self._worker_install.finished.connect(self._on_install_done)
        self._worker_install.start()

    def _on_install_done(self, success):
        self.install_btn.setEnabled(True)
        if success:
            self.install_log.append("\nAll installations complete!")
        else:
            self.install_log.append("\nSome installations failed. Check log above.")
        self._refresh_devices()


# ─── Main Window ───────────────────────────────────────────────────────────────
class ScoutTransferGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FRC 6369 · Scout Transfer")
        self.setMinimumSize(900, 700)
        self.resize(1000, 760)

        # Determine a safe, writeable location for the database
        from platformdirs import user_documents_dir
        safe_dir = Path(user_documents_dir()) / "ScoutTransfer"
        safe_dir.mkdir(parents=True, exist_ok=True)
        
        self.db_path = str(safe_dir / core.DB_FILE)
        self.conn = core.init_db(self.db_path)
        self.serial_thread = None
        self.scan_count = 0
        self.dupe_count = 0
        self.error_count = 0

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(10)

        # ── Header ──
        header = QHBoxLayout()
        title = QLabel("◆ SCOUT TRANSFER")
        title.setStyleSheet(
            f"font-size: 16px; font-weight: 700; color: {COLORS['red']}; letter-spacing: 2px;"
        )
        subtitle = QLabel("FRC 6369 MERCENARIES")
        subtitle.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 10px; letter-spacing: 3px;")
        header.addWidget(title)
        header.addWidget(subtitle)
        header.addStretch()
        
        self.toggle_manual_btn = QPushButton("Toggle Manual Entry")
        self.toggle_manual_btn.setCheckable(True)
        self.toggle_manual_btn.clicked.connect(self._toggle_manual_entry)
        header.addWidget(self.toggle_manual_btn)

        root.addLayout(header)

        # ── Status Bar ──
        self._build_status_bar(root)

        # ── Top-level tabs: Scanner | Tablet Manager ──
        self.main_tabs = QTabWidget()
        self.main_tabs.setStyleSheet(
            f"QTabBar::tab {{ padding: 10px 30px; font-size: 13px; font-weight: 600; }}"
        )

        # === Scanner Tab ===
        scanner_page = QWidget()
        scanner_layout = QVBoxLayout(scanner_page)
        scanner_layout.setContentsMargins(0, 8, 0, 0)
        scanner_layout.setSpacing(0)

        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(2)
        splitter.setStyleSheet(f"QSplitter::handle {{ background-color: {COLORS['border']}; }}")

        # Top section
        top = QWidget()
        top_layout = QVBoxLayout(top)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(8)

        self._build_serial_controls(top_layout)
        self._build_manual_entry(top_layout)
        self._build_scan_log(top_layout)

        splitter.addWidget(top)

        # Bottom section
        bottom = QWidget()
        bottom_layout = QVBoxLayout(bottom)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(8)

        self._build_data_tabs(bottom_layout)
        self._build_action_bar(bottom_layout)

        splitter.addWidget(bottom)
        splitter.setSizes([340, 360])

        scanner_layout.addWidget(splitter)
        self.main_tabs.addTab(scanner_page, "  Scanner  ")

        # === Tablet Manager Tab ===
        self.tablet_manager = TabletManagerWidget()
        self.main_tabs.addTab(self.tablet_manager, "  Tablet Manager  ")

        root.addWidget(self.main_tabs, stretch=1)

        # ── Initial refresh ──
        self._refresh_all()

        # ── Port refresh timer ──
        self.port_timer = QTimer(self)
        self.port_timer.timeout.connect(self._refresh_ports)
        self.port_timer.start(3000)

    # ── Status Bar ──────────────────────────────────────────────────────────
    def _build_status_bar(self, parent_layout):
        group = QFrame()
        group.setStyleSheet(
            f"background-color: {COLORS['surface']}; "
            f"border: 1px solid {COLORS['border']}; "
            f"border-radius: 8px; padding: 8px 14px;"
        )
        layout = QHBoxLayout(group)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(4)

        self.status_scanner = StatusDot("Scanner: Not Connected", COLORS["red"])
        self.status_db = StatusDot("DB: —", COLORS["text_dim"])
        self.status_pyserial = StatusDot(
            "pyserial: " + ("Installed" if core.serial else "Missing"),
            COLORS["green"] if core.serial else COLORS["red"],
        )
        self.status_last = StatusDot("Last: waiting...", COLORS["text_dim"])

        sep1 = QLabel("│")
        sep1.setStyleSheet(f"color: {COLORS['border_lt']}; font-size: 14px;")
        sep2 = QLabel("│")
        sep2.setStyleSheet(f"color: {COLORS['border_lt']}; font-size: 14px;")
        sep3 = QLabel("│")
        sep3.setStyleSheet(f"color: {COLORS['border_lt']}; font-size: 14px;")

        layout.addWidget(self.status_scanner)
        layout.addWidget(sep1)
        layout.addWidget(self.status_db)
        layout.addWidget(sep2)
        layout.addWidget(self.status_pyserial)
        layout.addWidget(sep3)
        layout.addWidget(self.status_last)
        layout.addStretch()

        parent_layout.addWidget(group)

    # ── Serial Controls ─────────────────────────────────────────────────────
    def _build_serial_controls(self, parent_layout):
        group = QGroupBox("SCANNER CONNECTION")
        layout = QHBoxLayout(group)
        layout.setSpacing(8)

        lbl_port = QLabel("Port:")
        lbl_port.setStyleSheet(f"color: {COLORS['text_dim']};")
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(200)
        self._refresh_ports()

        lbl_baud = QLabel("Baud:")
        lbl_baud.setStyleSheet(f"color: {COLORS['text_dim']};")
        self.baud_combo = QComboBox()
        bauds = [9600, 19200, 38400, 57600, 115200, 230400]
        for b in bauds:
            self.baud_combo.addItem(str(b), b)
        self.baud_combo.setCurrentText("115200")

        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setObjectName("connectBtn")
        self.connect_btn.clicked.connect(self._connect_serial)

        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.setObjectName("disconnectBtn")
        self.disconnect_btn.setEnabled(False)
        self.disconnect_btn.clicked.connect(self._disconnect_serial)

        self.refresh_ports_btn = QPushButton("Refresh")
        self.refresh_ports_btn.setFixedWidth(36)
        self.refresh_ports_btn.setToolTip("Refresh port list")
        self.refresh_ports_btn.clicked.connect(self._refresh_ports)

        layout.addWidget(lbl_port)
        layout.addWidget(self.port_combo, stretch=1)
        layout.addWidget(self.refresh_ports_btn)
        layout.addWidget(lbl_baud)
        layout.addWidget(self.baud_combo)
        layout.addWidget(self.connect_btn)
        layout.addWidget(self.disconnect_btn)

        parent_layout.addWidget(group)

    def _build_manual_entry(self, parent_layout):
        self.manual_group = QGroupBox("MANUAL ENTRY")
        layout = QHBoxLayout(self.manual_group)
        layout.setSpacing(8)

        self.manual_input = QLineEdit()
        self.manual_input.setPlaceholderText("Paste QR data here (e.g. match||9999||RonCollins||blue||1||...)  ")
        self.manual_input.returnPressed.connect(self._submit_manual)

        self.submit_btn = QPushButton("Submit")
        self.submit_btn.setFixedWidth(90)
        self.submit_btn.clicked.connect(self._submit_manual)

        layout.addWidget(self.manual_input, stretch=1)
        layout.addWidget(self.submit_btn)

        self.manual_group.setVisible(False)  # Hidden by default
        parent_layout.addWidget(self.manual_group)

    def _toggle_manual_entry(self, checked):
        self.manual_group.setVisible(checked)

    # ── Scan Log ────────────────────────────────────────────────────────────
    def _build_scan_log(self, parent_layout):
        group = QGroupBox("SCAN LOG")
        layout = QVBoxLayout(group)

        self.scan_log = QTextEdit()
        self.scan_log.setReadOnly(True)
        self.scan_log.setMaximumHeight(160)
        self.scan_log.setStyleSheet(
            f"background-color: {COLORS['bg']}; border: 1px solid {COLORS['border']}; "
            f"border-radius: 6px; font-size: 12px; line-height: 1.5;"
        )
        self.scan_log.setHtml(
            f"<div style='color:{COLORS['text_dim']}; padding: 8px;'>"
            "Ready — connect a scanner or paste data manually.</div>"
        )

        layout.addWidget(self.scan_log)
        parent_layout.addWidget(group)

    # ── Data Tabs ───────────────────────────────────────────────────────────
    def _build_data_tabs(self, parent_layout):
        self.tabs = QTabWidget()

        self.tables = {}
        for form_name in core.FIELDS:
            table = QTableWidget()
            table.setAlternatingRowColors(True)
            table.setStyleSheet(
                f"QTableWidget {{ alternate-background-color: {COLORS['surface2']}; }}"
            )
            table.setSelectionBehavior(QTableWidget.SelectRows)
            table.setEditTriggers(QTableWidget.DoubleClicked)
            table.horizontalHeader().setStretchLastSection(True)
            table.verticalHeader().setVisible(False)
            table.setContextMenuPolicy(Qt.CustomContextMenu)

            table.itemChanged.connect(self._on_table_item_changed)
            table.customContextMenuRequested.connect(self._on_table_context_menu)

            self.tables[form_name] = table
            self.tabs.addTab(table, f"  {form_name.upper()}  ")

        parent_layout.addWidget(self.tabs, stretch=1)

    # ── Action Bar ──────────────────────────────────────────────────────────
    def _build_action_bar(self, parent_layout):
        bar = QHBoxLayout()
        bar.setSpacing(10)

        self.export_btn = QPushButton("Export CSV")
        self.export_btn.setObjectName("exportBtn")
        self.export_btn.clicked.connect(self._export_csv)

        self.clear_btn = QPushButton("Clear Database")
        self.clear_btn.setObjectName("clearBtn")
        self.clear_btn.clicked.connect(self._clear_db)

        self.db_label = QLabel()
        self.db_label.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px;")
        self._update_db_label()

        self.change_db_btn = QPushButton("Change DB")
        self.change_db_btn.clicked.connect(self._change_db)

        bar.addWidget(self.export_btn)
        bar.addWidget(self.clear_btn)
        bar.addStretch()
        bar.addWidget(self.db_label)
        bar.addWidget(self.change_db_btn)

        parent_layout.addLayout(bar)

    # ═══════════════════════════════════════════════════════════════════════
    # Actions
    # ═══════════════════════════════════════════════════════════════════════

    def _refresh_ports(self):
        current = self.port_combo.currentText()
        self.port_combo.clear()
        ports = core.list_serial_ports()
        if ports:
            for p in ports:
                self.port_combo.addItem(f"{p.device}  ({p.description})", p.device)
            # Restore selection if still available
            idx = self.port_combo.findText(current, Qt.MatchStartsWith)
            if idx >= 0:
                self.port_combo.setCurrentIndex(idx)
        else:
            self.port_combo.addItem("No ports found")

    def _connect_serial(self):
        if core.serial is None:
            self._log_error("pyserial is not installed. Run: pip install pyserial")
            return

        port = self.port_combo.currentData()
        if not port:
            self._log_error("No serial port selected.")
            return

        baud = self.baud_combo.currentData()

        self.serial_thread = SerialReaderThread(port, baud)
        self.serial_thread.line_received.connect(self._on_serial_line)
        self.serial_thread.error_occurred.connect(self._on_serial_error)
        self.serial_thread.disconnected.connect(self._on_serial_disconnected)
        self.serial_thread.start()

        self.connect_btn.setEnabled(False)
        self.disconnect_btn.setEnabled(True)
        self.port_combo.setEnabled(False)
        self.baud_combo.setEnabled(False)

        self.status_scanner.set_status(
            f"Scanner: Connected ({port} @ {baud})", COLORS["green"]
        )
        self._log_info(f"Connected to {port} at {baud} baud. Scanning...")

    def _disconnect_serial(self):
        if self.serial_thread:
            self.serial_thread.stop()
            self.serial_thread.wait(2000)
            self.serial_thread = None

        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
        self.port_combo.setEnabled(True)
        self.baud_combo.setEnabled(True)

        self.status_scanner.set_status("Scanner: Disconnected", COLORS["red"])
        self._log_info("Scanner disconnected.")

    def _on_serial_line(self, line: str):
        self._process_line(line)

    def _on_serial_error(self, error: str):
        self._log_error(f"Serial error: {error}")
        self.status_scanner.set_status(f"Scanner: Error", COLORS["red"])

    def _on_serial_disconnected(self):
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
        self.port_combo.setEnabled(True)
        self.baud_combo.setEnabled(True)

    def _submit_manual(self):
        text = self.manual_input.text().strip()
        if not text:
            return
        self.manual_input.clear()
        self._process_line(text)

    def _process_line(self, line: str):
        """Process one scanned line — core logic with GUI feedback."""
        form, row, error = core.parse_scan(line)

        if form is None and error is None:
            return  # blank

        timestamp = datetime.now().strftime("%H:%M:%S")

        if error:
            self.error_count += 1
            self._log_error(f"{error}")
            self._refresh_status()
            return

        team = row.get("team", row.get("team1", "?"))
        inserted = core.insert_row(self.conn, form, row)

        if inserted:
            self.scan_count += 1
            self._log_success(f"{form.upper()}  team {team}  →  saved")
        else:
            self.dupe_count += 1
            self._log_warn(f"{form.upper()}  team {team}  →  duplicate, skipped")

        self.status_last.set_status(
            f"Last: {form} #{team} @ {timestamp}", COLORS["blue"]
        )
        self._refresh_all()

    def _on_table_item_changed(self, item):
        if getattr(self, "_is_refreshing_tables", False):
            return
            
        table = item.tableWidget()
        form_name = next((name for name, t in self.tables.items() if t == table), None)
        if not form_name:
            return
            
        row = item.row()
        col = item.column()
        new_val = item.text()
        col_name = table.horizontalHeaderItem(col).text()
        
        rowid_col = -1
        for c in range(table.columnCount()):
            if table.horizontalHeaderItem(c).text() == "rowid":
                rowid_col = c
                break
                
        if rowid_col == -1:
            self._log_error("Could not find rowid column. Cannot update row.")
            return
            
        if col == rowid_col:
            self._log_warn("Editing the internal rowid is not permitted.")
            self._refresh_tables()
            return
            
        rowid_val = table.item(row, rowid_col).text()
        
        try:
            cur = self.conn.cursor()
            cur.execute(f"UPDATE {form_name} SET {col_name} = ? WHERE rowid = ?", (new_val, rowid_val))
            self.conn.commit()
            self._log_info(f"Updated {form_name}.{col_name} to '{new_val}' (row {rowid_val})")
        except Exception as e:
            self._log_error(f"Error updating database: {e}")
            self.conn.rollback()
            self._refresh_tables()

    def _on_table_context_menu(self, pos):
        table = self.sender()
        item = table.itemAt(pos)
        if not item:
            return

        menu = QMenu(self)
        delete_action = menu.addAction("Delete Selected Row(s)")
        
        action = menu.exec(table.viewport().mapToGlobal(pos))
        if action == delete_action:
            form_name = next((name for name, t in self.tables.items() if t == table), None)
            if not form_name:
                return
                
            selected_rows = set(i.row() for i in table.selectedItems())
            if not selected_rows:
                return
                
            rowid_col = -1
            for c in range(table.columnCount()):
                if table.horizontalHeaderItem(c).text() == "rowid":
                    rowid_col = c
                    break
                    
            if rowid_col == -1:
                return
                
            reply = QMessageBox.warning(
                self,
                "Delete Row(s)",
                f"Are you sure you want to permanently delete {len(selected_rows)} record(s) from the database?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                cur = self.conn.cursor()
                deleted = 0
                for r in selected_rows:
                    rowid_val = table.item(r, rowid_col).text()
                    cur.execute(f"DELETE FROM {form_name} WHERE rowid = ?", (rowid_val,))
                    deleted += 1
                self.conn.commit()
                self._log_success(f"Deleted {deleted} row(s) from {form_name}.")
                self._refresh_all()

    def _export_csv(self):
        results = core.export_csv(self.conn, os.path.dirname(self.db_path) or ".")

        msg_lines = []
        any_data = False
        for form, path, count in results:
            if count > 0:
                any_data = True
                msg_lines.append(f"✓  {form.upper()}: {count} rows → {path}")
            else:
                msg_lines.append(f"  {form.upper()}: empty, skipped")

        if any_data:
            self._log_success("CSV export complete!")
            QMessageBox.information(
                self,
                "Export Complete ✓",
                "\n".join(msg_lines),
            )
        else:
            self._log_warn("No data to export.")
            QMessageBox.warning(self, "Export", "No data to export.")

    def _clear_db(self):
        reply = QMessageBox.warning(
            self,
            "Clear Database",
            "Are you sure you want to PERMANENTLY delete all records from the current database?\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            cur = self.conn.cursor()
            for form in core.FIELDS:
                cur.execute(f"DELETE FROM {form}")
            self.conn.commit()
            self.scan_count = 0
            self.dupe_count = 0
            self.error_count = 0
            self._log_info("Database cleared.")
            self._refresh_all()

    def _change_db(self):
        reply = QMessageBox.warning(
            self,
            "Change Database",
            "Are you sure you want to change the active database file?\nThis will disconnect from the current database.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            path, _ = QFileDialog.getOpenFileName(
                self, "Select Database", "", "SQLite DB (*.db);;All Files (*)"
            )
            if path:
                self.conn.close()
                self.db_path = os.path.abspath(path)
                self.conn = core.init_db(self.db_path)
                self.scan_count = 0
                self.dupe_count = 0
                self.error_count = 0
                self._log_info(f"Switched to database: {self.db_path}")
                self._refresh_all()

    # ═══════════════════════════════════════════════════════════════════════
    # UI Helpers
    # ═══════════════════════════════════════════════════════════════════════

    def _log_success(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self.scan_log.append(
            f"<span style='color:{COLORS['green']}'>SUCCESS:</span> "
            f"<span style='color:{COLORS['text']}'>{msg}</span>"
            f"<span style='color:{COLORS['text_dim']}; float:right;'>  {ts}</span>"
        )
        self.scan_log.verticalScrollBar().setValue(
            self.scan_log.verticalScrollBar().maximum()
        )

    def _log_warn(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self.scan_log.append(
            f"<span style='color:{COLORS['yellow']}'>WARN:</span> "
            f"<span style='color:{COLORS['yellow']}'>{msg}</span>"
            f"<span style='color:{COLORS['text_dim']}; float:right;'>  {ts}</span>"
        )
        self.scan_log.verticalScrollBar().setValue(
            self.scan_log.verticalScrollBar().maximum()
        )

    def _log_error(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self.scan_log.append(
            f"<span style='color:{COLORS['red']}'>ERROR:</span> "
            f"<span style='color:{COLORS['red']}'>{msg}</span>"
            f"<span style='color:{COLORS['text_dim']}; float:right;'>  {ts}</span>"
        )
        self.scan_log.verticalScrollBar().setValue(
            self.scan_log.verticalScrollBar().maximum()
        )

    def _log_info(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self.scan_log.append(
            f"<span style='color:{COLORS['blue']}'>INFO:</span> "
            f"<span style='color:{COLORS['text_dim']}'>{msg}</span>"
            f"<span style='color:{COLORS['text_dim']}; float:right;'>  {ts}</span>"
        )
        self.scan_log.verticalScrollBar().setValue(
            self.scan_log.verticalScrollBar().maximum()
        )

    def _refresh_all(self):
        """Refresh status bar, data tables, and DB info."""
        self._refresh_status()
        self._refresh_tables()
        self._update_db_label()

    def _refresh_status(self):
        """Update the status bar indicators."""
        counts = {}
        total = 0
        for form in core.FIELDS:
            c = core.row_count(self.conn, form)
            counts[form] = c
            total += c

        parts = [f"{f.upper()}: {c}" for f, c in counts.items()]
        db_text = "DB: " + " · ".join(parts)
        color = COLORS["green"] if total > 0 else COLORS["text_dim"]
        self.status_db.set_status(db_text, color)

    def _refresh_tables(self):
        """Reload all data tables from the database."""
        self._is_refreshing_tables = True
        try:
            for form_name, table in self.tables.items():
                cur = self.conn.cursor()
                cur.execute(f"SELECT * FROM {form_name}")
                rows = cur.fetchall()
                headers = [desc[0] for desc in cur.description]

                table.setColumnCount(len(headers))
                table.setHorizontalHeaderLabels(headers)
                table.setRowCount(len(rows))

                for r, row in enumerate(rows):
                    for c, val in enumerate(row):
                        item = QTableWidgetItem(str(val) if val is not None else "")
                        item.setToolTip(str(val) if val is not None else "NULL")
                        table.setItem(r, c, item)

                table.resizeColumnsToContents()
        finally:
            self._is_refreshing_tables = False

    def _update_db_label(self):
        self.db_label.setText(f"📁 {self.db_path}")

    def closeEvent(self, event):
        """Clean up on window close."""
        if self.serial_thread:
            self.serial_thread.stop()
            self.serial_thread.wait(2000)
        if self.conn:
            self.conn.close()
        event.accept()


# ─── Entry Point ───────────────────────────────────────────────────────────────
def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLESHEET)

    # Use team icon if available
    base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    icon_path = os.path.join(base_dir, "icons", "mercs.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = ScoutTransferGUI()
    window.raise_()
    window.activateWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
