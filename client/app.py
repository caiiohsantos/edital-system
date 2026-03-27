# client/app.py
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QScrollArea, QFrame,
    QSizePolicy, QStackedWidget, QMessageBox, QFileDialog,
    QButtonGroup, QGridLayout, QDialog,
)
from PySide6.QtCore import Qt, QThread, Signal, QUrl, QTimer, QSize
from PySide6.QtGui import QFont, QColor, QPalette, QCursor, QDesktopServices

from core.database import ClientDB
from core.utils import (
    get_mac_hash, format_date_br, format_datetime_br,
    days_remaining, is_expired, make_youtube_html, is_youtube_url,
)
from core.license_core import (
    load_license_from_file, validate_license_data, find_license_file,
)
from core.editals_data import EDITALS_DATA, PRIORITY_COLORS, PRIORITY_LABELS
from client.updater import check_for_updates, get_current_version

import subprocess
import shutil
import threading

# ------------------------------------------------------------------
#  WEBENGINE — embutido no PySide6, nao precisa instalar nada extra
# ------------------------------------------------------------------
try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6.QtWebEngineCore import QWebEngineSettings, QWebEngineProfile
    import os as _os
    _os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--disable-logging")
    WEB_ENGINE_AVAILABLE = True
except Exception:
    WEB_ENGINE_AVAILABLE = False

# ------------------------------------------------------------------
#  EDGE FALLBACK — abre janela externa se WebEngine nao disponivel
# ------------------------------------------------------------------
def _find_edge():
    for p in [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]:
        if os.path.exists(p):
            return p
    return shutil.which("msedge")

EDGE_PATH = _find_edge()

def open_edge_app(url: str):
    def _run():
        if EDGE_PATH:
            subprocess.Popen([EDGE_PATH, f"--app={url}", "--window-size=1100,680"])
        else:
            QDesktopServices.openUrl(QUrl(url))
    threading.Thread(target=_run, daemon=True).start()

# ==================================================================
#  STYLES
# ==================================================================
CLIENT_STYLE = """
QMainWindow, QDialog, QWidget {
    background-color: #0d1117;
    color: #c9d1d9;
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
}
QLabel { color: #c9d1d9; }
QLabel#app_title  { font-size: 20px; font-weight: bold; color: #e6edf3; }
QLabel#user_info  { font-size: 12px; color: #8b949e; }
QLabel#license_ok   { color: #2ea043; font-weight: 600; font-size: 12px; }
QLabel#license_warn { color: #d29922; font-weight: 600; font-size: 12px; }
QLabel#license_err  { color: #f85149; font-weight: 600; font-size: 12px; }
QLabel#card_title   { font-size: 13px; font-weight: 600; color: #e6edf3; }
QLabel#card_meta    { font-size: 11px; color: #8b949e; }

QLineEdit, QComboBox {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 6px 12px;
    color: #c9d1d9;
    selection-background-color: #1f6feb;
}
QLineEdit:focus, QComboBox:focus { border-color: #58a6ff; }
QComboBox::drop-down { border: none; width: 24px; }
QComboBox QAbstractItemView {
    background: #161b22; border: 1px solid #30363d;
    color: #c9d1d9; selection-background-color: #21262d;
}

QPushButton {
    background-color: #21262d; color: #c9d1d9;
    border: 1px solid #30363d; border-radius: 6px;
    padding: 5px 12px; font-size: 12px; font-weight: 500;
}
QPushButton:hover   { background-color: #30363d; }
QPushButton:pressed { background-color: #161b22; }
QPushButton#btn_edital {
    background-color: #1f2d3d; color: #58a6ff; border-color: #1f6feb;
}
QPushButton#btn_edital:hover { background-color: #1f6feb; color: white; }
QPushButton#btn_consulta {
    background-color: #1d2d1d; color: #3fb950; border-color: #238636;
}
QPushButton#btn_consulta:hover { background-color: #238636; color: white; }
QPushButton#btn_tutorial {
    background-color: #2d1d2d; color: #bc8cff; border-color: #6e40c9;
}
QPushButton#btn_tutorial:hover  { background-color: #6e40c9; color: white; }
QPushButton#btn_tutorial:disabled {
    background-color: #161b22; color: #30363d; border-color: #21262d;
}
QPushButton#primary {
    background-color: #1f6feb; color: white; border: none;
    padding: 10px 24px; font-size: 14px;
}
QPushButton#primary:hover { background-color: #388bfd; }
QPushButton#filter_btn {
    border-radius: 14px; padding: 4px 14px; font-size: 12px;
}
QPushButton#filter_btn:checked {
    background-color: #1f6feb; color: white; border-color: #1f6feb;
}

QFrame#card {
    background-color: #161b22; border: 1px solid #30363d; border-radius: 10px;
}
QFrame#header_bar {
    background-color: #161b22; border-bottom: 1px solid #30363d;
}
QFrame#search_bar {
    background-color: #161b22; border-bottom: 1px solid #21262d;
}
QScrollArea { border: none; background: transparent; }
QScrollBar:vertical { background: #0d1117; width: 8px; border-radius: 4px; }
QScrollBar::handle:vertical { background: #30363d; border-radius: 4px; min-height: 20px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
"""

# ==================================================================
#  WORKERS
# ==================================================================
class UpdateCheckWorker(QThread):
    found    = Signal(dict)
    finished = Signal()
    def __init__(self, url):
        super().__init__()
        self.url = url
    def run(self):
        data = check_for_updates(self.url)
        if data:
            self.found.emit(data)
        self.finished.emit()

class OpenUrlWorker(QThread):
    def __init__(self, url):
        super().__init__()
        self.url = url
    def run(self):
        QDesktopServices.openUrl(QUrl(self.url))

# ==================================================================
#  LICENSE SCREEN
# ==================================================================
class LicenseScreen(QWidget):
    activation_success = Signal(dict)

    def __init__(self, db, initial_msg=""):
        super().__init__()
        self.db = db
        self._initial_msg = initial_msg
        self._build()
        if initial_msg:
            self._set_msg(initial_msg, error=True)
    def _build(self):
        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignCenter)

        card = QFrame()
        card.setObjectName("card")
        card.setFixedWidth(480)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(40, 40, 40, 40)
        cl.setSpacing(18)

        icon = QLabel("🚦")
        icon.setAlignment(Qt.AlignCenter)
        icon.setFont(QFont("Segoe UI", 48))
        cl.addWidget(icon)

        t = QLabel("Edital System")
        t.setAlignment(Qt.AlignCenter)
        t.setStyleSheet("font-size:24px;font-weight:bold;color:#58a6ff;")
        cl.addWidget(t)

        ver = QLabel(f"v{get_current_version()}")
        ver.setAlignment(Qt.AlignCenter)
        ver.setStyleSheet("color:#8b949e;font-size:12px;")
        cl.addWidget(ver)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background:#30363d;")
        sep.setFixedHeight(1)
        cl.addWidget(sep)

        info = QLabel("Importe o arquivo de licenca (.lic)\nfornecido pelo administrador.")
        info.setAlignment(Qt.AlignCenter)
        info.setStyleSheet("color:#8b949e;font-size:12px;")
        cl.addWidget(info)

        btn = QPushButton("Importar Arquivo de Licenca (.lic)")
        btn.setObjectName("primary")
        btn.setFixedHeight(44)
        btn.clicked.connect(self._import)
        cl.addWidget(btn)

        self.msg = QLabel("")
        self.msg.setAlignment(Qt.AlignCenter)
        self.msg.setWordWrap(True)
        cl.addWidget(self.msg)

        ar = QHBoxLayout()
        al = QLabel("Ja tem .lic na pasta?")
        al.setStyleSheet("color:#8b949e;font-size:11px;")
        db = QPushButton("Detectar")
        db.setStyleSheet("font-size:11px;padding:3px 10px;")
        db.clicked.connect(self._auto)
        ar.addStretch(); ar.addWidget(al); ar.addWidget(db); ar.addStretch()
        cl.addLayout(ar)

        lay.addWidget(card)

    def _auto(self):
        p = find_license_file()
        if p:
            self._activate(str(p))
        else:
            self._set_msg("Nenhum .lic encontrado.", True)

    def _import(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Licenca", "", "Arquivo de Licenca (*.lic)"
        )
        if path:
            self._activate(path)

    def _activate(self, path):
        try:
            data = load_license_from_file(path)
            mac  = get_mac_hash()
            ok, msg = validate_license_data(data, mac)
            if ok:
                self.db.save_license(data["serial"], data["user_name"],
                                     data["valid_until"], mac)
                self._set_msg(f"Licenca ativada! {msg}", False)
                QTimer.singleShot(1500, lambda: self.activation_success.emit(data))
            else:
                self._set_msg(msg, True)
        except Exception as e:
            self._set_msg(str(e), True)

    def _set_msg(self, txt, err=True):
        self.msg.setStyleSheet(f"color:{'#f85149' if err else '#2ea043'};font-size:12px;")
        self.msg.setText(txt)

# ------------------------------------------------------------------
#  URL type detection
# ------------------------------------------------------------------
def _detect_url_type(url: str) -> str:
    """
    Detecta o tipo de URL para escolher o player correto.

    Suportado como VIDEO DIRETO (toca inline no app):
      - Cloudflare R2:  https://pub-xxx.r2.dev/video.mp4
      - Qualquer CDN:   https://cdn.exemplo.com/video.mp4
      - Bunny.net CDN:  https://xxx.b-cdn.net/video.mp4
      - GitHub Releases: https://github.com/.../releases/.../video.mp4
      - Arquivo local:  detran_mg.mp4  (sem http)
      - Qualquer URL terminando em .mp4 / .webm / .ogg / .mov

    Abre no NAVEGADOR:
      - YouTube (embed bloqueado pelo YT)
      - Google Drive (requer login)
      - Outros links nao reconhecidos
    """
    if not url:
        return "empty"

    # Arquivo local (sem http) — pasta tutoriais/
    if not url.startswith("http"):
        return "local"

    url_lower = url.lower()

    # YouTube
    if "youtube.com" in url_lower or "youtu.be" in url_lower:
        return "youtube"

    # Google Drive (requer login, abre no navegador)
    if "drive.google.com" in url_lower:
        return "browser"

    # Extensao de video direta — toca inline
    VIDEO_EXTS = (".mp4", ".webm", ".ogg", ".mov", ".mkv", ".avi")
    if any(url_lower.split("?")[0].endswith(ext) for ext in VIDEO_EXTS):
        return "direct"

    # CDNs conhecidos que servem video direto
    VIDEO_CDNS = (
        "r2.dev",           # Cloudflare R2
        "b-cdn.net",        # Bunny.net
        "cloudfront.net",   # AWS CloudFront
        "githubusercontent.com",  # GitHub raw
        "backblazeb2.com",  # Backblaze B2
        "digitaloceanspaces.com",
        "s3.amazonaws.com",
    )
    if any(cdn in url_lower for cdn in VIDEO_CDNS):
        return "direct"

    return "browser"

def _gdrive_file_id(url: str) -> str:
    import re
    m = re.search(r"/d/([a-zA-Z0-9_-]{10,})", url)
    return m.group(1) if m else ""

def _gdrive_to_preview(url: str) -> str:
    fid = _gdrive_file_id(url)
    if fid:
        return f"https://drive.google.com/file/d/{fid}/preview"
    return url

def _make_video_html(stream_url: str) -> str:
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#0d1117;display:flex;justify-content:center;
align-items:center;height:100vh;overflow:hidden}}
video{{max-width:100%;max-height:100vh;border-radius:8px;outline:none}}</style>
</head><body>
<video controls autoplay preload="metadata">
<source src="{stream_url}">
</video></body></html>"""

# ------------------------------------------------------------------
#  LOCAL VIDEO SERVER
#  Serve videos da pasta /tutoriais via http://localhost:PORT
#  O WebEngine carrega sem nenhuma restricao ou erro
# ------------------------------------------------------------------
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
import pathlib as _pathlib


# ==================================================================
#  THUMBNAIL WORKER (YouTube)
# ==================================================================
class ThumbnailWorker(QThread):
    ready = Signal(bytes)

    def __init__(self, video_id: str):
        super().__init__()
        self.video_id = video_id

    def run(self):
        import urllib.request
        for q in ["maxresdefault", "hqdefault", "mqdefault", "default"]:
            try:
                url = f"https://img.youtube.com/vi/{self.video_id}/{q}.jpg"
                with urllib.request.urlopen(url, timeout=6) as r:
                    data = r.read()
                if len(data) > 1000:
                    self.ready.emit(data)
                    return
            except Exception:
                continue


# ==================================================================
#  TUTORIAL PANEL
#  - Arquivo local (.mp4 na pasta tutoriais/) -> QMediaPlayer nativo
#  - URL direta de video (CDN/R2/etc)         -> QMediaPlayer nativo
#  - YouTube                                  -> card + abre navegador
# ==================================================================
class TutorialPanel(QWidget):
    closed = Signal()

    def __init__(self):
        super().__init__()
        self._url    = ""
        self._nome   = ""
        self._worker = None
        self._build()

    def _build(self):
        self._lay = QVBoxLayout(self)
        self._lay.setContentsMargins(0, 0, 0, 0)
        self._lay.setSpacing(0)

        # Header
        hdr = QFrame()
        hdr.setObjectName("header_bar")
        hdr.setFixedHeight(50)
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(16, 0, 16, 0)
        self.title_lbl = QLabel("Tutorial")
        self.title_lbl.setStyleSheet("font-weight:bold;font-size:14px;")
        hl.addWidget(self.title_lbl)
        hl.addStretch()
        back = QPushButton("Voltar")
        back.clicked.connect(self._on_back)
        hl.addWidget(back)
        self._lay.addWidget(hdr)

        # Player nativo Qt (MP4 local ou URL direta)
        self._video = QVideoWidget()
        self._video.setStyleSheet("background:#000;")
        self._player = QMediaPlayer()
        self._audio  = QAudioOutput()
        self._player.setAudioOutput(self._audio)
        self._player.setVideoOutput(self._video)
        self._audio.setVolume(1.0)
        self._video.hide()
        self._lay.addWidget(self._video, 1)

        # Card YouTube
        self._yt_card = self._make_yt_card()
        self._yt_card.hide()
        self._lay.addWidget(self._yt_card, 1)

        # Placeholder
        self._ph = QLabel("Selecione um tutorial")
        self._ph.setAlignment(Qt.AlignCenter)
        self._ph.setStyleSheet("color:#8b949e;font-size:14px;")
        self._lay.addWidget(self._ph, 1)

    def _make_yt_card(self) -> QWidget:
        w = QWidget()
        cl = QVBoxLayout(w)
        cl.setAlignment(Qt.AlignCenter)
        cl.setSpacing(16)
        cl.setContentsMargins(40, 40, 40, 40)

        card = QFrame()
        card.setFixedSize(400, 280)
        card.setStyleSheet(
            "QFrame{background:#1a1a1a;border-radius:12px;}"
            "QFrame:hover{background:#222;}"
        )
        card.setCursor(QCursor(Qt.PointingHandCursor))
        cl2 = QVBoxLayout(card)
        cl2.setContentsMargins(0, 0, 0, 0)
        cl2.setSpacing(0)

        self._thumb = QLabel()
        self._thumb.setFixedSize(400, 225)
        self._thumb.setAlignment(Qt.AlignCenter)
        self._thumb.setStyleSheet("background:#0d1117;border-radius:12px 12px 0 0;")
        self._draw_play()
        cl2.addWidget(self._thumb)

        info = QWidget()
        info.setStyleSheet("background:#1a1a1a;border-radius:0 0 12px 12px;")
        il = QHBoxLayout(info)
        il.setContentsMargins(12, 8, 12, 10)
        ico = QLabel("▶")
        ico.setStyleSheet("color:#ff0000;font-size:18px;")
        ico.setFixedWidth(24)
        il.addWidget(ico)
        self._yt_name = QLabel("Tutorial")
        self._yt_name.setStyleSheet("color:#e6edf3;font-size:12px;font-weight:600;")
        self._yt_name.setWordWrap(True)
        il.addWidget(self._yt_name, 1)
        cl2.addWidget(info)

        card.mousePressEvent = lambda _: self._open_browser()
        self._thumb.mousePressEvent = lambda _: self._open_browser()
        cl.addWidget(card)

        note = QLabel("YouTube nao permite embed — clique para abrir no navegador")
        note.setAlignment(Qt.AlignCenter)
        note.setStyleSheet(
            "color:#8b949e;font-size:11px;"
            "background:#21262d;border-radius:6px;padding:5px 14px;"
        )
        cl.addWidget(note, alignment=Qt.AlignCenter)

        btn = QPushButton("Assistir no YouTube")
        btn.setFixedSize(200, 40)
        btn.setStyleSheet(
            "QPushButton{background:#ff0000;color:white;border:none;"
            "border-radius:8px;font-size:13px;font-weight:bold;}"
            "QPushButton:hover{background:#cc0000;}"
        )
        btn.clicked.connect(self._open_browser)
        cl.addWidget(btn, alignment=Qt.AlignCenter)
        return w

    def _draw_play(self):
        from PySide6.QtGui import QPixmap, QPainter, QBrush, QPolygon
        from PySide6.QtCore import QPoint
        pix = QPixmap(400, 225)
        pix.fill(QColor("#0d1117"))
        p = QPainter(pix)
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(QBrush(QColor("#ff0000")))
        p.setPen(Qt.NoPen)
        p.drawEllipse(162, 87, 76, 52)
        p.setBrush(QBrush(QColor("white")))
        p.drawPolygon(QPolygon([QPoint(188,101),QPoint(188,125),QPoint(215,113)]))
        p.end()
        self._thumb.setPixmap(pix)

    def load_tutorial(self, url: str, nome: str):
        self._url  = url
        self._nome = nome
        self.title_lbl.setText(f"Tutorial  {nome}")

        self._ph.hide()
        self._yt_card.hide()
        self._video.hide()
        self._player.stop()

        if not url:
            self._ph.show()
            return

        # YouTube -> card
        if "youtube.com" in url or "youtu.be" in url:
            self._yt_name.setText(nome)
            self._draw_play()
            self._yt_card.show()
            self._fetch_thumb(url)
            return

        # Arquivo local na pasta tutoriais/
        if not url.startswith("http"):
            tdir = _pathlib.Path(__file__).parent.parent / "tutoriais"
            path = tdir / _pathlib.Path(url.strip()).name
            media_url = QUrl.fromLocalFile(str(path))
        else:
            # URL direta (CDN, R2, Bunny, GitHub Releases, etc.)
            media_url = QUrl(url)

        self._player.setSource(media_url)
        self._video.show()
        self._player.play()

    def _fetch_thumb(self, url):
        from core.utils import extract_youtube_id
        vid = extract_youtube_id(url)
        if not vid:
            return
        if self._worker:
            self._worker.quit()
        self._worker = ThumbnailWorker(vid)
        self._worker.ready.connect(self._on_thumb)
        self._worker.start()

    def _on_thumb(self, data: bytes):
        from PySide6.QtGui import QPixmap
        pix = QPixmap()
        pix.loadFromData(data)
        if not pix.isNull():
            pix = pix.scaled(400, 225, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            x = (pix.width()-400)//2
            y = (pix.height()-225)//2
            self._thumb.setPixmap(pix.copy(x, y, 400, 225))

    def _open_browser(self):
        if self._url:
            QDesktopServices.openUrl(QUrl(self._url))

    def _on_back(self):
        self._player.stop()
        self.closed.emit()


# ==================================================================
#  EDITAL CARD
# ==================================================================
class EditalCard(QFrame):
    tutorial_requested = Signal(str, str)

    def __init__(self, edital, priority, db, last_verified=None):
        super().__init__()
        self.edital        = edital
        self.priority      = priority
        self.db            = db
        self.last_verified = last_verified
        self._workers      = []
        self._build()

    def _build(self):
        self.setObjectName("card")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        pc = PRIORITY_COLORS.get(self.priority, "#8b949e")
        self.setStyleSheet(
            f"QFrame#card{{background:#161b22;border:1px solid #30363d;"
            f"border-left:3px solid {pc};border-radius:10px;}}"
            f"QFrame#card:hover{{border-color:{pc}55;border-left-color:{pc};}}"
        )

        ml = QVBoxLayout(self)
        ml.setContentsMargins(16, 12, 16, 12)
        ml.setSpacing(8)

        # Top row
        top = QHBoxLayout()
        self.dot = QLabel("●")
        self.dot.setFixedWidth(16)
        top.addWidget(self.dot)

        ttl = QLabel(self.edital["nome"])
        ttl.setObjectName("card_title")
        ttl.setWordWrap(True)
        top.addWidget(ttl, 1)

        estado = self.edital.get("estado", "")
        if estado:
            b = QLabel(estado)
            b.setStyleSheet(
                f"background:{pc}22;color:{pc};"
                "border-radius:4px;padding:2px 7px;font-size:11px;font-weight:bold;"
            )
            b.setFixedHeight(20)
            top.addWidget(b)
        ml.addLayout(top)

        self.verified_lbl = QLabel()
        self.verified_lbl.setObjectName("card_meta")
        ml.addWidget(self.verified_lbl)
        self._update_dot()

        # Buttons
        br = QHBoxLayout()
        br.setSpacing(6)

        def _add_btn(label, obj_name, url, action):
            if not url:
                return
            btn = QPushButton(label)
            btn.setObjectName(obj_name)
            btn.setFixedHeight(30)
            btn.clicked.connect(lambda: self._open(url, action))
            br.addWidget(btn)

        _add_btn("Edital",    "btn_edital",   self.edital.get("edital_url", ""),    "edital")
        _add_btn("Consulta",  "btn_consulta", self.edital.get("consulta_url", ""),  "consulta")
        _add_btn("Consulta 2","btn_consulta", self.edital.get("consulta_url2", ""), "consulta")

        tut_url = self.edital.get("tutorial_url", "")
        tb = QPushButton("Tutorial")
        tb.setObjectName("btn_tutorial")
        tb.setFixedHeight(30)
        tb.setEnabled(bool(tut_url))
        tb.clicked.connect(lambda: self.tutorial_requested.emit(tut_url, self.edital["nome"]))
        br.addWidget(tb)
        self.tut_btn = tb

        br.addStretch()
        ml.addLayout(br)

    def _open(self, url, action):
        w = OpenUrlWorker(url)
        self._workers.append(w)
        w.finished.connect(lambda: self._workers.remove(w) if w in self._workers else None)
        w.start()
        self.db.mark_verified(self.edital["id"], action)
        self.last_verified = self.db.get_last_verification(self.edital["id"])
        self._update_dot()

    def _update_dot(self):
        if self.last_verified:
            self.dot.setStyleSheet("color:#2ea043;font-size:14px;")
            self.verified_lbl.setStyleSheet("color:#2ea043;font-size:11px;")
            self.verified_lbl.setText(f"Verificado em {format_datetime_br(self.last_verified)}")
        else:
            self.dot.setStyleSheet("color:#f85149;font-size:14px;")
            self.verified_lbl.setStyleSheet("color:#8b949e;font-size:11px;")
            self.verified_lbl.setText("Nao verificado")

    def update_tutorial_url(self, url):
        self.edital["tutorial_url"] = url
        self.tut_btn.setEnabled(bool(url))
        self.tut_btn.clicked.disconnect()
        self.tut_btn.clicked.connect(lambda: self.tutorial_requested.emit(url, self.edital["nome"]))

    def matches_search(self, q):
        q = q.lower()
        return (q in self.edital["nome"].lower() or
                q in self.edital.get("estado", "").lower() or
                q in self.edital.get("tipo", "").lower())

# ==================================================================
#  MAIN EDITAIS VIEW
# ==================================================================
class EditaisView(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db    = db
        self.cards = []
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Search bar
        sb = QFrame()
        sb.setObjectName("search_bar")
        sb.setFixedHeight(56)
        sbl = QHBoxLayout(sb)
        sbl.setContentsMargins(20, 8, 20, 8)
        sbl.setSpacing(12)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Buscar edital, estado ou tipo...")
        self.search.setFixedHeight(36)
        self.search.textChanged.connect(self._filter)
        self.search.setMinimumWidth(260)
        sbl.addWidget(self.search)

        self.filter_group = QButtonGroup(self)
        self.filter_group.setExclusive(True)
        for lbl, val in [("Todos", None), ("P1", "Prioridade 1"),
                         ("P2", "Prioridade 2"), ("P3", "Prioridade 3"),
                         ("P4", "Prioridade 4")]:
            b = QPushButton(lbl)
            b.setObjectName("filter_btn")
            b.setCheckable(True)
            b.setFixedHeight(30)
            b.setProperty("fv", val)
            b.clicked.connect(self._filter)
            self.filter_group.addButton(b)
            sbl.addWidget(b)

        self.filter_group.buttons()[0].setChecked(True)
        sbl.addStretch()

        self.count_lbl = QLabel("")
        self.count_lbl.setStyleSheet("color:#8b949e;font-size:12px;")
        sbl.addWidget(self.count_lbl)
        lay.addWidget(sb)

        # Stack: cards / tutorial
        self.stack = QStackedWidget()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.cards_w = QWidget()
        self.cards_w.setStyleSheet("background:transparent;")
        self.cards_l = QVBoxLayout(self.cards_w)
        self.cards_l.setContentsMargins(20, 16, 20, 20)
        self.cards_l.setSpacing(8)
        self.cards_l.addStretch()
        scroll.setWidget(self.cards_w)
        self.stack.addWidget(scroll)

        self.tut_panel = TutorialPanel()
        self.tut_panel.closed.connect(lambda: self.stack.setCurrentIndex(0))
        self.stack.addWidget(self.tut_panel)

        lay.addWidget(self.stack)
        self.refresh_cards()

    def refresh_cards(self):
        from core.tutorials_sync import load_tutorials
        verifications = self.db.get_all_verifications()
        tutorials     = load_tutorials()

        while self.cards_l.count() > 1:
            item = self.cards_l.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.cards = []
        for prio, editals in EDITALS_DATA.items():
            hdr = QLabel(PRIORITY_LABELS.get(prio, prio))
            hdr.setStyleSheet(
                f"color:{PRIORITY_COLORS.get(prio,'#c9d1d9')};"
                "font-size:13px;font-weight:bold;padding:12px 0 4px 0;"
            )
            self.cards_l.insertWidget(self.cards_l.count() - 1, hdr)

            for e in editals:
                merged = dict(e)
                merged["tutorial_url"] = tutorials.get(e["id"], e.get("tutorial_url", ""))
                card = EditalCard(merged, prio, self.db, verifications.get(e["id"]))
                card.tutorial_requested.connect(self._show_tutorial)
                self.cards_l.insertWidget(self.cards_l.count() - 1, card)
                self.cards.append(card)

        self._update_count()

    def _show_tutorial(self, url, nome):
        self.tut_panel.load_tutorial(url, nome)
        self.stack.setCurrentIndex(1)

    def _filter(self):
        q  = self.search.text().strip()
        fv = next((b.property("fv") for b in self.filter_group.buttons()
                   if b.isChecked()), None)
        visible = 0
        for c in self.cards:
            show = True
            if q and not c.matches_search(q):
                show = False
            if fv and c.priority != fv:
                show = False
            c.setVisible(show)
            if show:
                visible += 1
        self._update_count(visible)

    def _update_count(self, n=None):
        n = n if n is not None else len(self.cards)
        self.count_lbl.setText(f"{n} / {len(self.cards)} editais")

# ==================================================================
#  MAIN WINDOW
# ==================================================================
class MainWindow(QMainWindow):
    def __init__(self, db, license_data):
        super().__init__()
        self.db           = db
        self.license_data = license_data
        self._workers     = []
        self.setWindowTitle("Edital System")
        self.setMinimumSize(1100, 700)
        self._build()
        self._check_updates()

    def _build(self):
        central = QWidget()
        self.setCentralWidget(central)
        lay = QVBoxLayout(central)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Header
        hdr = QFrame()
        hdr.setObjectName("header_bar")
        hdr.setFixedHeight(60)
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(20, 0, 20, 0)
        hl.setSpacing(16)

        ic = QLabel("🚦")
        ic.setFont(QFont("Segoe UI", 22))
        hl.addWidget(ic)

        ti = QLabel("Edital System")
        ti.setObjectName("app_title")
        hl.addWidget(ti)
        hl.addStretch()

        user   = self.license_data.get("user_name", "Usuario")
        valid  = self.license_data.get("valid_until", "")
        dr     = days_remaining(valid)
        ds     = format_date_br(valid)

        ul = QLabel(f"👤 {user}")
        ul.setObjectName("user_info")
        hl.addWidget(ul)

        hl.addWidget(self._sep())

        if dr < 0:
            ll = QLabel("Licenca Expirada"); ll.setObjectName("license_err")
        elif dr <= 7:
            ll = QLabel(f"Expira em {dr} dias ({ds})"); ll.setObjectName("license_warn")
        else:
            ll = QLabel(f"Licenca valida ate {ds}"); ll.setObjectName("license_ok")
        hl.addWidget(ll)
        hl.addWidget(self._sep())

        # WebEngine status badge
        if WEB_ENGINE_AVAILABLE:
            we_lbl = QLabel("Player embutido ativo")
            we_lbl.setStyleSheet(
                "background:#1d2d1d;color:#2ea043;border-radius:4px;"
                "padding:3px 8px;font-size:11px;"
            )
        else:
            we_lbl = QLabel("Modo externo (Edge)")
            we_lbl.setStyleSheet(
                "background:#2d2000;color:#d29922;border-radius:4px;"
                "padding:3px 8px;font-size:11px;"
            )
        hl.addWidget(we_lbl)
        hl.addWidget(self._sep())

        ref_btn = QPushButton("🔄")
        ref_btn.setFixedSize(32, 32)
        ref_btn.setToolTip("Recarregar tutoriais")
        ref_btn.clicked.connect(self._reload)
        hl.addWidget(ref_btn)

        cfg_btn = QPushButton("⚙")
        cfg_btn.setFixedSize(32, 32)
        cfg_btn.setToolTip("Configuracoes")
        cfg_btn.clicked.connect(self._settings)
        hl.addWidget(cfg_btn)

        lay.addWidget(hdr)

        self.ev = EditaisView(self.db)
        lay.addWidget(self.ev)

        # Status bar
        stb = QFrame()
        stb.setFixedHeight(26)
        stb.setStyleSheet("background:#161b22;border-top:1px solid #21262d;")
        stl = QHBoxLayout(stb)
        stl.setContentsMargins(16, 0, 16, 0)

        self.ver_lbl = QLabel(f"v{get_current_version()} — Sistema de Editais")
        self.ver_lbl.setStyleSheet("color:#8b949e;font-size:11px;")
        stl.addWidget(self.ver_lbl)
        stl.addStretch()

        self.status_lbl = QLabel("Pronto")
        self.status_lbl.setStyleSheet("color:#8b949e;font-size:11px;")
        stl.addWidget(self.status_lbl)
        lay.addWidget(stb)

    def _sep(self):
        s = QLabel("|")
        s.setStyleSheet("color:#30363d;")
        return s

    def _reload(self):
        self.ev.refresh_cards()
        self.status_lbl.setText("Tutoriais atualizados!")
        QTimer.singleShot(3000, lambda: self.status_lbl.setText("Pronto"))

    def _check_updates(self):
        pass  # configure update_url here if needed

    def _settings(self):
        d = SettingsDialog(self, self.db, self.license_data)
        d.exec()

# ==================================================================
#  SETTINGS DIALOG
# ==================================================================
class SettingsDialog(QDialog):
    def __init__(self, parent, db, license_data):
        super().__init__(parent)
        self.db           = db
        self.license_data = license_data
        self.setWindowTitle("Configuracoes")
        self.setMinimumWidth(460)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(16)

        t = QLabel("Configuracoes")
        t.setStyleSheet("font-size:18px;font-weight:bold;color:#58a6ff;")
        lay.addWidget(t)

        sec = QLabel("Informacoes da Licenca")
        sec.setStyleSheet("color:#58a6ff;font-weight:bold;font-size:13px;"
                          "border-bottom:1px solid #30363d;padding-bottom:6px;")
        lay.addWidget(sec)

        g = QGridLayout()
        for i, (lbl, val) in enumerate([
            ("Usuario:", self.license_data.get("user_name", "—")),
            ("Serial:", self.license_data.get("serial", "—")),
            ("Valido ate:", format_date_br(self.license_data.get("valid_until", ""))),
        ]):
            l = QLabel(lbl); l.setStyleSheet("color:#8b949e;")
            v = QLabel(val); v.setStyleSheet("color:#e6edf3;font-weight:500;")
            g.addWidget(l, i, 0); g.addWidget(v, i, 1)
        lay.addLayout(g)

        imp = QPushButton("Importar Nova Licenca")
        imp.clicked.connect(self._reimport)
        lay.addWidget(imp)

        clr = QPushButton("Limpar Licenca (desativar)")
        clr.setStyleSheet("color:#f85149;border-color:#f85149;")
        clr.clicked.connect(self._clear)
        lay.addWidget(clr)

        lay.addStretch()
        close = QPushButton("Fechar")
        close.setObjectName("primary")
        close.clicked.connect(self.accept)
        lay.addWidget(close)

    def _reimport(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Licenca", "", "Arquivo de Licenca (*.lic)"
        )
        if path:
            try:
                data = load_license_from_file(path)
                mac  = get_mac_hash()
                ok, msg = validate_license_data(data, mac)
                if ok:
                    self.db.save_license(data["serial"], data["user_name"],
                                         data["valid_until"], mac)
                    QMessageBox.information(self, "Sucesso",
                        f"Licenca importada!\n{msg}\nReinicie o app.")
                    self.accept()
                else:
                    QMessageBox.warning(self, "Invalida", msg)
            except Exception as e:
                QMessageBox.critical(self, "Erro", str(e))

    def _clear(self):
        if QMessageBox.question(self, "Confirmar",
            "Limpar licenca? Precisara reativar.",
            QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.db.clear_license()
            self.accept()
            QApplication.quit()

# ==================================================================
#  APP ENTRY
# ==================================================================
class ClientApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Edital System")
        self.setMinimumSize(960, 650)
        self.db   = ClientDB()
        self._stk = QStackedWidget()
        self.setCentralWidget(self._stk)
        self._check_license()

    def _check_license(self):
        """
        Valida licenca em 3 camadas:
        1. Existe no banco local?
        2. Ainda esta dentro da validade e MAC correto?
        3. Nao foi bloqueada/revogada pelo admin?
        Se qualquer check falhar -> tela de ativacao.
        """
        lic = self.db.get_license()
        if not lic:
            self._show_activation()
            return

        data = dict(lic)
        from core.license_core import validate_license_data
        mac = get_mac_hash()
        ok, msg = validate_license_data({
            "serial":     data["serial_key"],
            "user_name":  data["user_name"],
            "valid_until":data["valid_until"],
            "mac_hash":   data["mac_hash"],
        }, mac)

        if not ok:
            # Licenca invalida/expirada/MAC diferente -> limpa e pede ativacao
            self.db.clear_license()
            self._show_activation(msg)
            return

        # Verifica revogacao remota (lista de seriais bloqueados no GitHub)
        if self._is_revoked(data["serial_key"]):
            self.db.clear_license()
            self._show_activation(
                "Sua licenca foi cancelada pelo administrador. Entre em contato para reativar."
            )
            return

        self._show_main({
            "serial":     data["serial_key"],
            "user_name":  data["user_name"],
            "valid_until":data["valid_until"],
            "issued_at":  data.get("activated_at", ""),
        })

    def _is_revoked(self, serial: str) -> bool:
        """
        Consulta lista de seriais bloqueados no GitHub.
        Se offline, permite acesso (beneficio da duvida).
        """
        from core.tutorials_sync import GITHUB_TUTORIALS_URL
        if not GITHUB_TUTORIALS_URL:
            return False
        try:
            import urllib.request, json
            base = GITHUB_TUTORIALS_URL.rsplit("/", 1)[0]
            url  = base + "/blocked_serials.json"
            with urllib.request.urlopen(url, timeout=4) as r:
                data = json.loads(r.read().decode())
            blocked = data.get("blocked", [])
            return serial in blocked
        except Exception:
            return False  # offline = permite

    def _show_activation(self, msg: str = ""):
        ls = LicenseScreen(self.db, initial_msg=msg)
        ls.activation_success.connect(self._show_main)
        self._stk.addWidget(ls)
        self._stk.setCurrentWidget(ls)

    def _show_main(self, ld):
        if hasattr(self, "_mw"):
            return
        self._mw = MainWindow(self.db, ld)
        self._stk.addWidget(self._mw.centralWidget())
        self._stk.setCurrentIndex(self._stk.count() - 1)
        self.setWindowTitle(f"Edital System — {ld.get('user_name','')}")


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    pal = QPalette()
    pal.setColor(QPalette.Window,          QColor("#0d1117"))
    pal.setColor(QPalette.WindowText,      QColor("#c9d1d9"))
    pal.setColor(QPalette.Base,            QColor("#161b22"))
    pal.setColor(QPalette.AlternateBase,   QColor("#0d1117"))
    pal.setColor(QPalette.Text,            QColor("#c9d1d9"))
    pal.setColor(QPalette.Button,          QColor("#21262d"))
    pal.setColor(QPalette.ButtonText,      QColor("#c9d1d9"))
    pal.setColor(QPalette.Highlight,       QColor("#1f6feb"))
    pal.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    app.setPalette(pal)
    app.setStyleSheet(CLIENT_STYLE)

    win = ClientApp()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
