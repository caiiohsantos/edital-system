# client/app.py — Edital System v4 (Linear-style dark)
import sys, os, json, urllib.request, pathlib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QScrollArea, QFrame,
    QSizePolicy, QStackedWidget, QMessageBox, QFileDialog,
    QButtonGroup, QDialog, QGridLayout,
)
from PySide6.QtCore import Qt, QThread, Signal, QUrl, QTimer
from PySide6.QtGui import (
    QFont, QColor, QPalette, QCursor, QDesktopServices,
    QPixmap, QPainter, QBrush, QPolygon, QRadialGradient,
)
from PySide6.QtCore import QPoint
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput, QMediaDevices
from PySide6.QtMultimediaWidgets import QVideoWidget

from core.database import ClientDB
from core.utils import (
    get_mac_hash, format_date_br, format_datetime_br,
    days_remaining, extract_youtube_id,
)
from core.license_core import (
    load_license_from_file, validate_license_data, find_license_file,
)
from core.editals_data import PRIORITY_COLORS, PRIORITY_LABELS
try:
    from core.custom_editals import get_all_editals_merged
    EDITALS_DATA = get_all_editals_merged()
except Exception:
    from core.editals_data import EDITALS_DATA
from client.updater import check_for_updates, APP_VERSION

GITHUB_URL = "https://raw.githubusercontent.com/caiiohsantos/edital-system/master/tutorials.json"

# ══════════════════════════════════════════════════════════════════
#  PALETTE — Linear-style dark
# ══════════════════════════════════════════════════════════════════
C = {
    "bg":       "#0B0C10",
    "sidebar":  "#0B0C10",
    "surface":  "#15171D",
    "surface2": "#1B1E26",
    "border":   "#232530",
    "border2":  "#2D303D",
    "text":     "#F2F2F0",
    "text2":    "#9094A0",
    "text3":    "#6B6C76",
    "accent":   "#7F77DD",
    "accent2":  "#9A93E8",
    "green":    "#5DCAA5",
    "green_bg": "#1D2B26",
    "red":      "#E9776F",
    "red_bg":   "#2A1A1A",
    "yellow":   "#EF9F27",
    "blue":     "#85B7EB",
    "blue_bg":  "#15212E",
    "green2":   "#97C459",
    "green2_bg":"#1C2417",
    "p1": "#E24B4A", "p2": "#EF9F27", "p3": "#378ADD",
    "p4": "#888780", "pref": "#7F77DD",
}

STYLE = f"""
* {{ font-family: 'Segoe UI', sans-serif; }}
QMainWindow, QDialog {{ background:{C['bg']}; color:{C['text']}; }}
QWidget {{ background:transparent; color:{C['text']}; font-size:13px; }}
QScrollArea, QScrollArea > QWidget > QWidget {{ background:transparent; border:none; }}

QLineEdit {{
    background:{C['surface']}; border:1px solid {C['border']};
    border-radius:8px; padding:7px 12px; color:{C['text']};
}}
QLineEdit:focus {{ border-color:{C['accent']}; }}

QPushButton {{
    background:{C['surface']}; color:{C['text2']};
    border:1px solid {C['border']}; border-radius:7px;
    padding:6px 13px; font-size:12px; font-weight:500;
}}
QPushButton:hover {{ background:{C['surface2']}; color:{C['text']}; border-color:{C['border2']}; }}
QPushButton:pressed {{ background:{C['bg']}; }}

QPushButton#primary {{
    background:{C['accent']}; color:#0B0C10; border:none;
    border-radius:8px; padding:10px 26px; font-size:14px; font-weight:600;
}}
QPushButton#primary:hover {{ background:{C['accent2']}; }}

QPushButton#chip {{
    background:{C['surface']}; color:{C['text3']};
    border:1px solid {C['border']}; border-radius:20px;
    padding:5px 14px; font-size:11px; font-weight:500;
}}
QPushButton#chip:hover {{ color:{C['text2']}; border-color:{C['border2']}; }}
QPushButton#chip:checked {{
    background:{C['accent']}; color:#0B0C10; border-color:{C['accent']}; font-weight:600;
}}

QPushButton#iconbtn {{
    background:{C['surface']}; border:1px solid {C['border']};
    border-radius:8px; padding:0;
}}
QPushButton#iconbtn:hover {{ background:{C['surface2']}; border-color:{C['border2']}; }}

QPushButton#navicon {{
    background:transparent; border:none; border-radius:10px; padding:0;
}}
QPushButton#navicon:hover {{ background:{C['surface2']}; }}
QPushButton#navicon:checked {{ background:{C['surface2']}; }}

QPushButton#link_edital {{
    background:transparent; color:{C['blue']}; border:1px solid #2B4159;
    border-radius:8px; padding:0; font-size:12px; font-weight:500;
}}
QPushButton#link_edital:hover {{ background:{C['blue_bg']}; }}

QPushButton#como_acessar {{
    background:transparent; color:{C['text2']}; border:1px solid {C['border']};
    border-radius:8px; padding:0; font-size:12px;
}}
QPushButton#como_acessar:hover {{ background:{C['surface2']}; color:{C['text']}; }}
QPushButton#como_acessar:disabled {{ color:{C['text3']}; border-color:{C['border']}; }}

QPushButton#consulta_ait {{
    background:transparent; color:{C['green2']}; border:1px solid #2D4A2B;
    border-radius:8px; padding:0; font-size:12px; font-weight:500;
}}
QPushButton#consulta_ait:hover {{ background:{C['green2_bg']}; }}

QPushButton#como_consultar {{
    background:transparent; color:{C['text2']}; border:1px solid {C['border']};
    border-radius:8px; padding:0; font-size:12px;
}}
QPushButton#como_consultar:hover {{ background:{C['surface2']}; color:{C['text']}; }}
QPushButton#como_consultar:disabled {{ color:{C['text3']}; border-color:{C['border']}; }}

QScrollBar:vertical {{ background:{C['bg']}; width:5px; border-radius:3px; }}
QScrollBar::handle:vertical {{ background:{C['border2']}; border-radius:3px; min-height:24px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0; }}
"""


# ══════════════════════════════════════════════════════════════════
#  WORKERS
# ══════════════════════════════════════════════════════════════════
class UrlResolverWorker(QThread):
    resolved = Signal(str)
    def __init__(self, url): super().__init__(); self.url = url
    def run(self):
        if not self.url.startswith("http"):
            self.resolved.emit(self.url); return
        try:
            req = urllib.request.Request(self.url, method="HEAD",
                headers={"User-Agent":"Mozilla/5.0 Chrome/124.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                self.resolved.emit(r.url)
        except Exception:
            self.resolved.emit(self.url)


class ThumbnailWorker(QThread):
    ready = Signal(bytes)
    def __init__(self, vid): super().__init__(); self.vid = vid
    def run(self):
        for q in ["maxresdefault","hqdefault","mqdefault","default"]:
            try:
                url = f"https://img.youtube.com/vi/{self.vid}/{q}.jpg"
                with urllib.request.urlopen(url, timeout=6) as r:
                    data = r.read()
                if len(data) > 1000: self.ready.emit(data); return
            except Exception: continue


class UpdateWorker(QThread):
    found = Signal(dict)
    def __init__(self, url): super().__init__(); self.url = url
    def run(self):
        data = check_for_updates(self.url)
        if data: self.found.emit(data)


# ══════════════════════════════════════════════════════════════════
#  ICON HELPERS  (drawn glyphs, no external font needed)
# ══════════════════════════════════════════════════════════════════
def icon_label(glyph: str, size=16, color=None) -> QLabel:
    lbl = QLabel(glyph)
    lbl.setAlignment(Qt.AlignCenter)
    c = color or C["text2"]
    lbl.setStyleSheet(f"background:transparent;color:{c};font-size:{size}px;")
    return lbl


# ══════════════════════════════════════════════════════════════════
#  LICENSE SCREEN
# ══════════════════════════════════════════════════════════════════
class LicenseScreen(QWidget):
    activation_success = Signal(dict)

    def __init__(self, db, msg=""):
        super().__init__()
        self.db = db
        self.setStyleSheet(f"background:{C['bg']};")
        self._build()
        if msg: self._set_msg(msg, True)

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignCenter)

        card = QWidget()
        card.setFixedWidth(420)
        card.setStyleSheet(f"""
            QWidget {{ background:{C['surface']}; border-radius:16px; border:1px solid {C['border']}; }}
        """)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(40, 40, 40, 40)
        cl.setSpacing(16)

        logo = QLabel("⚖")
        logo.setAlignment(Qt.AlignCenter)
        logo.setStyleSheet(f"font-size:38px;color:{C['accent']};background:transparent;")
        cl.addWidget(logo)

        title = QLabel("Edital System")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"font-size:22px;font-weight:600;color:{C['text']};background:transparent;")
        cl.addWidget(title)

        ver = QLabel(f"Versão {APP_VERSION}")
        ver.setAlignment(Qt.AlignCenter)
        ver.setStyleSheet(f"font-size:12px;color:{C['text3']};background:transparent;")
        cl.addWidget(ver)

        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"background:{C['border']};max-height:1px;")
        cl.addWidget(sep)

        hint = QLabel("Importe o arquivo de licença (.lic)\nfornecido pelo administrador.")
        hint.setAlignment(Qt.AlignCenter); hint.setWordWrap(True)
        hint.setStyleSheet(f"font-size:13px;color:{C['text2']};background:transparent;")
        cl.addWidget(hint)

        btn = QPushButton("Importar Licença (.lic)")
        btn.setObjectName("primary"); btn.setFixedHeight(44)
        btn.clicked.connect(self._import)
        cl.addWidget(btn)

        auto = QPushButton("Detectar automaticamente")
        auto.setStyleSheet(f"background:transparent;border:none;color:{C['text3']};font-size:11px;")
        auto.clicked.connect(self._auto)
        cl.addWidget(auto, alignment=Qt.AlignCenter)

        self.msg_lbl = QLabel("")
        self.msg_lbl.setAlignment(Qt.AlignCenter); self.msg_lbl.setWordWrap(True)
        self.msg_lbl.setStyleSheet("background:transparent;")
        cl.addWidget(self.msg_lbl)

        lay.addWidget(card)

    def _import(self):
        path,_ = QFileDialog.getOpenFileName(self,"Licença","","*.lic")
        if path: self._activate(path)

    def _auto(self):
        p = find_license_file()
        if p: self._activate(str(p))
        else: self._set_msg("Nenhum arquivo .lic encontrado.", True)

    def _activate(self, path):
        try:
            data = load_license_from_file(path)
            ok, msg = validate_license_data(data, get_mac_hash())
            if ok:
                self.db.save_license(data["serial"],data["user_name"],data["valid_until"],get_mac_hash())
                self._set_msg(f"✓ {msg}", False)
                QTimer.singleShot(1000, lambda: self.activation_success.emit(data))
            else:
                self._set_msg(f"✕ {msg}", True)
        except Exception as e:
            self._set_msg(f"✕ {e}", True)

    def _set_msg(self, txt, err):
        c = C["red"] if err else C["green"]
        self.msg_lbl.setStyleSheet(f"color:{c};font-size:12px;background:transparent;")
        self.msg_lbl.setText(txt)


# ══════════════════════════════════════════════════════════════════
#  VIDEO PANEL
# ══════════════════════════════════════════════════════════════════
class VideoPanel(QWidget):
    closed = Signal()

    def __init__(self, panel_title=""):
        super().__init__()
        self._url = ""
        self._resolver = None
        self._thumb_w  = None
        self._panel_title = panel_title
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0,0,0,0); lay.setSpacing(0)
        self.setStyleSheet(f"background:{C['bg']};")

        hdr = QWidget(); hdr.setFixedHeight(54)
        hdr.setStyleSheet(f"background:{C['surface']};border-bottom:1px solid {C['border']};")
        hl = QHBoxLayout(hdr); hl.setContentsMargins(24,0,24,0)

        back = QPushButton("←  Voltar")
        back.setStyleSheet(f"background:transparent;border:none;color:{C['accent2']};font-size:13px;font-weight:600;")
        back.clicked.connect(self.closed.emit)
        hl.addWidget(back)

        self.title_lbl = QLabel(self._panel_title)
        self.title_lbl.setStyleSheet(f"color:{C['text']};font-size:14px;font-weight:600;background:transparent;")
        hl.addWidget(self.title_lbl); hl.addStretch()
        lay.addWidget(hdr)

        self._video_w = QVideoWidget()
        self._video_w.setStyleSheet("background:#000;")
        self._player  = QMediaPlayer()
        self._audio   = QAudioOutput(QMediaDevices.defaultAudioOutput())
        self._audio.setVolume(1.0); self._audio.setMuted(False)
        self._player.setAudioOutput(self._audio)
        self._player.setVideoOutput(self._video_w)
        self._player.playbackStateChanged.connect(self._on_state)
        self._player.errorOccurred.connect(self._on_error)
        self._video_w.hide()
        lay.addWidget(self._video_w, 1)

        self._yt_w = self._make_yt_card()
        self._yt_w.hide()
        lay.addWidget(self._yt_w, 1)

        self._ph = QLabel("Nenhum vídeo selecionado")
        self._ph.setAlignment(Qt.AlignCenter)
        self._ph.setStyleSheet(f"color:{C['text3']};font-size:14px;background:transparent;")
        lay.addWidget(self._ph, 1)

    def _make_yt_card(self):
        w = QWidget(); w.setStyleSheet(f"background:{C['bg']};")
        cl = QVBoxLayout(w); cl.setAlignment(Qt.AlignCenter)
        cl.setSpacing(18); cl.setContentsMargins(40,40,40,40)

        card = QFrame(); card.setFixedSize(420,292)
        card.setStyleSheet(f"""
            QFrame {{ background:{C['surface']}; border:1px solid {C['border']}; border-radius:14px; }}
            QFrame:hover {{ background:{C['surface2']}; border-color:{C['border2']}; }}
        """)
        card.setCursor(QCursor(Qt.PointingHandCursor))
        cl2 = QVBoxLayout(card); cl2.setContentsMargins(0,0,0,0); cl2.setSpacing(0)

        self._thumb = QLabel(); self._thumb.setFixedSize(420,236)
        self._thumb.setAlignment(Qt.AlignCenter)
        self._thumb.setStyleSheet(f"background:{C['bg']};border-radius:14px 14px 0 0;")
        self._draw_play()
        cl2.addWidget(self._thumb)

        info = QWidget(); info.setStyleSheet(f"background:{C['surface']};border-radius:0 0 14px 14px;")
        il = QHBoxLayout(info); il.setContentsMargins(14,8,14,10)
        il.addWidget(icon_label("▶", 16, "#E9776F"))
        self._yt_name = QLabel("Tutorial")
        self._yt_name.setStyleSheet(f"color:{C['text']};font-size:12px;font-weight:600;background:transparent;")
        self._yt_name.setWordWrap(True)
        il.addWidget(self._yt_name, 1)
        cl2.addWidget(info)

        card.mousePressEvent = lambda _: QDesktopServices.openUrl(QUrl(self._url))
        self._thumb.mousePressEvent = lambda _: QDesktopServices.openUrl(QUrl(self._url))
        cl.addWidget(card)

        note = QLabel("O YouTube não permite incorporação — clique para abrir no navegador")
        note.setAlignment(Qt.AlignCenter)
        note.setStyleSheet(f"color:{C['text3']};font-size:11px;background:transparent;")
        cl.addWidget(note)

        btn = QPushButton("Assistir no YouTube")
        btn.setFixedSize(220,40)
        btn.setStyleSheet("""
            QPushButton { background:#c4302b; color:white; border:none;
                border-radius:8px; font-size:13px; font-weight:700; }
            QPushButton:hover { background:#e03128; }
        """)
        btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(self._url)))
        cl.addWidget(btn, alignment=Qt.AlignCenter)
        return w

    def _draw_play(self):
        pix = QPixmap(420,236); pix.fill(QColor(C["bg"]))
        p = QPainter(pix); p.setRenderHint(QPainter.Antialiasing)
        grad = QRadialGradient(210,118,120)
        grad.setColorAt(0, QColor("#1a0000")); grad.setColorAt(1, QColor(C["bg"]))
        p.fillRect(0,0,420,236,grad)
        p.setBrush(QBrush(QColor("#c4302b"))); p.setPen(Qt.NoPen)
        p.drawEllipse(172,90,76,56)
        p.setBrush(QBrush(QColor("white")))
        p.drawPolygon(QPolygon([QPoint(198,104),QPoint(198,130),QPoint(226,117)]))
        p.end()
        self._thumb.setPixmap(pix)

    def load(self, url: str, title: str):
        self._url = url
        self.title_lbl.setText(title)
        self._ph.hide(); self._yt_w.hide(); self._video_w.hide()
        self._player.stop()

        if not url:
            self._ph.show(); return

        if "youtube.com" in url or "youtu.be" in url:
            self._yt_name.setText(title); self._draw_play(); self._yt_w.show()
            vid = extract_youtube_id(url)
            if vid:
                self._thumb_w = ThumbnailWorker(vid)
                self._thumb_w.ready.connect(self._on_thumb)
                self._thumb_w.start()
            return

        if not url.startswith("http"):
            tdir = pathlib.Path(__file__).parent.parent / "tutoriais"
            self._player.setSource(QUrl.fromLocalFile(str(tdir / pathlib.Path(url).name)))
            self._video_w.show(); self._player.play(); return

        self._video_w.show()
        self._resolver = UrlResolverWorker(url)
        self._resolver.resolved.connect(lambda u: (self._player.setSource(QUrl(u)), self._player.play()))
        self._resolver.start()

    def _on_state(self, state):
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self._audio.setMuted(False); self._audio.setVolume(1.0)

    def _on_error(self, err, msg):
        self._video_w.hide(); self._ph.setText(f"Erro: {msg}"); self._ph.show()

    def _on_thumb(self, data: bytes):
        pix = QPixmap(); pix.loadFromData(data)
        if not pix.isNull():
            pix = pix.scaled(420,236, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            x=(pix.width()-420)//2; y=(pix.height()-236)//2
            self._thumb.setPixmap(pix.copy(x,y,420,236))

    def stop(self): self._player.stop()


# ══════════════════════════════════════════════════════════════════
#  EDITAL CARD — Linear style: icon-square status + accordion
# ══════════════════════════════════════════════════════════════════
class EditalCard(QWidget):
    video_requested = Signal(str, str)

    def __init__(self, edital, priority, db, last_verified=None):
        super().__init__()
        self.edital = edital; self.priority = priority
        self.db = db; self.last_verified = last_verified
        self._expanded = False
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0,0,0,8); lay.setSpacing(0)

        self._card = QFrame()
        self._card.setStyleSheet(f"""
            QFrame {{ background:{C['surface']}; border:1px solid {C['border']}; border-radius:12px; }}
        """)
        card_lay = QVBoxLayout(self._card)
        card_lay.setContentsMargins(0,0,0,0); card_lay.setSpacing(0)

        # ── HEADER ROW ─────────────────────────────────────────
        self._hdr = QPushButton()
        self._hdr.setCheckable(True)
        self._hdr.setFixedHeight(62)
        self._hdr.setStyleSheet("""
            QPushButton { background:transparent; border:none; text-align:left; padding:0; }
            QPushButton:hover { background: rgba(255,255,255,8); }
        """)
        self._hdr.clicked.connect(self._toggle)

        hl = QHBoxLayout(self._hdr)
        hl.setContentsMargins(16,0,16,0); hl.setSpacing(12)

        # Status icon square
        self._status_sq = QLabel()
        self._status_sq.setFixedSize(32,32)
        self._status_sq.setAlignment(Qt.AlignCenter)
        hl.addWidget(self._status_sq)

        # Name + verified status
        col = QVBoxLayout(); col.setSpacing(2)
        name = QLabel(self.edital["nome"])
        name.setStyleSheet(f"font-size:14px;font-weight:600;color:{C['text']};background:transparent;")
        col.addWidget(name)
        self._status_lbl = QLabel("")
        self._status_lbl.setStyleSheet(f"font-size:11px;background:transparent;")
        col.addWidget(self._status_lbl)
        hl.addLayout(col, 1)

        # Estado badge
        est = self.edital.get("estado","")
        if est:
            color = PRIORITY_COLORS.get(self.priority, C["p4"])
            badge = QLabel(est)
            badge.setStyleSheet(f"""
                background:{color}26; color:{color};
                border-radius:6px; padding:4px 11px;
                font-size:11px; font-weight:600;
            """)
            hl.addWidget(badge)

        self._chev = icon_label("›", 18, C["text3"])
        self._chev.setFixedWidth(16)
        hl.addWidget(self._chev)

        card_lay.addWidget(self._hdr)

        # ── BODY ───────────────────────────────────────────────
        self._body = QFrame()
        self._body.setStyleSheet(f"background:transparent; border-top:1px solid {C['border']};")
        body_lay = QVBoxLayout(self._body)
        body_lay.setContentsMargins(16,12,16,16); body_lay.setSpacing(8)

        edital_url   = self.edital.get("edital_url","")
        acesso_url   = self.edital.get("acesso_url","")
        consulta_url = self.edital.get("consulta_url","")
        consulta_url2= self.edital.get("consulta_url2","")
        tut_url      = self.edital.get("tutorial_url","")

        row1 = QHBoxLayout(); row1.setSpacing(8)
        if edital_url:
            b1 = QPushButton("🔗  Link do Edital")
            b1.setObjectName("link_edital"); b1.setFixedHeight(34)
            b1.clicked.connect(lambda: self._open(edital_url,"edital"))
            row1.addWidget(b1,1)
        b2 = QPushButton("▶  Como Acessar o Edital")
        b2.setObjectName("como_acessar"); b2.setFixedHeight(34)
        b2.setEnabled(bool(acesso_url))
        b2.clicked.connect(lambda: self.video_requested.emit(
            self.edital.get("acesso_url",""), f"Como Acessar — {self.edital['nome']}"))
        self._acesso_btn = b2
        row1.addWidget(b2,1)
        body_lay.addLayout(row1)

        row2 = QHBoxLayout(); row2.setSpacing(8)
        if consulta_url:
            b3 = QPushButton("🔍  Consulta de AIT ou Processo")
            b3.setObjectName("consulta_ait"); b3.setFixedHeight(34)
            b3.clicked.connect(lambda: self._open(consulta_url,"consulta"))
            row2.addWidget(b3,1)
        if consulta_url2:
            b4 = QPushButton("🔍  Consulta 2")
            b4.setObjectName("consulta_ait"); b4.setFixedHeight(34)
            b4.clicked.connect(lambda: self._open(consulta_url2,"consulta"))
            row2.addWidget(b4,1)
        b5 = QPushButton("▶  Como Consultar AIT")
        b5.setObjectName("como_consultar"); b5.setFixedHeight(34)
        b5.setEnabled(bool(tut_url))
        b5.clicked.connect(lambda: self.video_requested.emit(
            self.edital.get("tutorial_url",""), f"Como Consultar — {self.edital['nome']}"))
        self._tut_btn = b5
        row2.addWidget(b5,1)
        body_lay.addLayout(row2)

        self._body.hide()
        card_lay.addWidget(self._body)
        lay.addWidget(self._card)
        self._update_status()

    def _toggle(self, checked):
        self._expanded = checked
        self._chev.setText("⌄" if checked else "›")
        self._body.setVisible(checked)

    def _open(self, url, action):
        QDesktopServices.openUrl(QUrl(url))
        self.db.mark_verified(self.edital["id"], action)
        self.last_verified = self.db.get_last_verification(self.edital["id"])
        self._update_status()

    def _update_status(self):
        if self.last_verified:
            self._status_sq.setStyleSheet(f"background:{C['green_bg']};border-radius:8px;")
            self._status_sq.setText("✓")
            self._status_sq.setStyleSheet(f"background:{C['green_bg']};border-radius:8px;color:{C['green']};font-size:15px;font-weight:700;")
            ts = format_datetime_br(self.last_verified)
            self._status_lbl.setText(f"Verificado em {ts}")
            self._status_lbl.setStyleSheet(f"color:{C['green']};font-size:11px;background:transparent;")
        else:
            self._status_sq.setText("○")
            self._status_sq.setStyleSheet(f"background:{C['red_bg']};border-radius:8px;color:{C['red']};font-size:15px;font-weight:700;")
            self._status_lbl.setText("Não verificado")
            self._status_lbl.setStyleSheet(f"color:{C['text3']};font-size:11px;background:transparent;")

    def update_urls(self, tut_url, acesso_url):
        self.edital["tutorial_url"] = tut_url
        self.edital["acesso_url"]   = acesso_url
        self._tut_btn.setEnabled(bool(tut_url))
        self._acesso_btn.setEnabled(bool(acesso_url))

    def matches(self, q):
        q = q.lower()
        return (q in self.edital["nome"].lower()
             or q in self.edital.get("estado","").lower()
             or q in self.edital.get("tipo","").lower())

    def is_verified(self):
        return bool(self.last_verified)


# ══════════════════════════════════════════════════════════════════
#  STAT CARD
# ══════════════════════════════════════════════════════════════════
class StatCard(QFrame):
    def __init__(self, label, value, color):
        super().__init__()
        self.setStyleSheet(f"""
            QFrame {{ background:{C['surface']}; border:1px solid {C['border']}; border-radius:10px; }}
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14,12,14,12); lay.setSpacing(2)
        self._val = QLabel(value)
        self._val.setStyleSheet(f"font-size:22px;font-weight:600;color:{color};background:transparent;")
        lay.addWidget(self._val)
        lbl = QLabel(label)
        lbl.setStyleSheet(f"font-size:12px;color:{C['text3']};background:transparent;")
        lay.addWidget(lbl)

    def set_value(self, v): self._val.setText(v)


# ══════════════════════════════════════════════════════════════════
#  EDITAIS PAGE
# ══════════════════════════════════════════════════════════════════
class EditaisPage(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.cards = []
        self._current_prio = None
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0,0,0,0); root.setSpacing(0)

        top = QWidget()
        tl = QVBoxLayout(top)
        tl.setContentsMargins(28,24,28,0); tl.setSpacing(0)

        hdr_row = QHBoxLayout()
        title_col = QVBoxLayout()
        title = QLabel("Editais")
        title.setStyleSheet(f"font-size:20px;font-weight:600;color:{C['text']};background:transparent;")
        title_col.addWidget(title)
        sub = QLabel("Acompanhe e consulte todos os processos")
        sub.setStyleSheet(f"font-size:13px;color:{C['text3']};background:transparent;")
        title_col.addWidget(sub)
        hdr_row.addLayout(title_col); hdr_row.addStretch()

        ref_btn = QPushButton("↻")
        ref_btn.setObjectName("iconbtn"); ref_btn.setFixedSize(34,34)
        ref_btn.setToolTip("Atualizar tutoriais")
        ref_btn.clicked.connect(self.refresh_cards)
        hdr_row.addWidget(ref_btn)

        self._settings_btn = QPushButton("⚙")
        self._settings_btn.setObjectName("iconbtn"); self._settings_btn.setFixedSize(34,34)
        hdr_row.addWidget(self._settings_btn)
        tl.addLayout(hdr_row)
        tl.addSpacing(18)

        # Stats row
        stats_row = QHBoxLayout(); stats_row.setSpacing(10)
        self.s_total = StatCard("Total de editais","0", C["text"])
        self.s_ver   = StatCard("Verificados","0", C["green"])
        self.s_pend  = StatCard("Pendentes","0", C["red"])
        self.s_pref  = StatCard("Prefeituras","0", C["accent"])
        for w in [self.s_total,self.s_ver,self.s_pend,self.s_pref]:
            stats_row.addWidget(w)
        tl.addLayout(stats_row)
        tl.addSpacing(16)

        # Search + filters
        sf_row = QHBoxLayout(); sf_row.setSpacing(8)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Buscar edital, estado ou tipo...")
        self.search.setFixedHeight(32); self.search.setMaximumWidth(280)
        self.search.textChanged.connect(self._filter)
        sf_row.addWidget(self.search)

        self.fg = QButtonGroup(self); self.fg.setExclusive(True)
        filters = [("Todos", None)] + [(p.replace("Prioridade ","P"), p) for p in EDITALS_DATA.keys()]
        for label, prio in filters:
            btn = QPushButton(label); btn.setObjectName("chip")
            btn.setCheckable(True); btn.setFixedHeight(28)
            btn.setProperty("prio", prio)
            btn.clicked.connect(self._filter)
            self.fg.addButton(btn); sf_row.addWidget(btn)
        self.fg.buttons()[0].setChecked(True)
        sf_row.addStretch()
        tl.addLayout(sf_row)

        root.addWidget(top)

        self.stack = QStackedWidget()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.cards_w = QWidget(); self.cards_w.setStyleSheet("background:transparent;")
        self.cards_l = QVBoxLayout(self.cards_w)
        self.cards_l.setContentsMargins(28,16,28,24); self.cards_l.setSpacing(4)
        self.cards_l.addStretch()
        scroll.setWidget(self.cards_w)
        self.stack.addWidget(scroll)

        self.vid_edital = VideoPanel("Como Acessar o Edital")
        self.vid_edital.closed.connect(lambda: self.stack.setCurrentIndex(0))
        self.stack.addWidget(self.vid_edital)

        self.vid_consulta = VideoPanel("Como Consultar AIT")
        self.vid_consulta.closed.connect(lambda: self.stack.setCurrentIndex(0))
        self.stack.addWidget(self.vid_consulta)

        root.addWidget(self.stack)
        self.refresh_cards()

    def refresh_cards(self):
        from core.tutorials_sync import load_tutorials
        tutorials = load_tutorials()
        verifs = self.db.get_all_verifications()

        while self.cards_l.count() > 1:
            item = self.cards_l.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        self.cards.clear()

        for prio, editals in EDITALS_DATA.items():
            color = PRIORITY_COLORS.get(prio, C["p4"])
            hdr = QLabel(PRIORITY_LABELS.get(prio, prio))
            hdr.setStyleSheet(f"color:{color};font-size:11px;font-weight:700;letter-spacing:1px;padding:14px 2px 6px 2px;background:transparent;")
            self.cards_l.insertWidget(self.cards_l.count()-1, hdr)

            for e in editals:
                merged = dict(e)
                merged["tutorial_url"] = tutorials.get(e["id"]+"_tut", e.get("tutorial_url",""))
                merged["acesso_url"]   = tutorials.get(e["id"]+"_acesso", e.get("acesso_url",""))
                card = EditalCard(merged, prio, self.db, verifs.get(e["id"]))
                card.video_requested.connect(self._on_video)
                self.cards_l.insertWidget(self.cards_l.count()-1, card)
                self.cards.append(card)

        self._update_stats()
        self._filter()

    def _on_video(self, url, title):
        if "Como Acessar" in title:
            self.vid_edital.load(url, title); self.stack.setCurrentIndex(1)
        else:
            self.vid_consulta.load(url, title); self.stack.setCurrentIndex(2)

    def _filter(self):
        q = self.search.text().strip()
        active = None
        for btn in self.fg.buttons():
            if btn.isChecked(): active = btn.property("prio"); break
        for card in self.cards:
            show = True
            if q and not card.matches(q): show = False
            if active and card.priority != active: show = False
            card.setVisible(show)

    def _update_stats(self):
        total = len(self.cards)
        ver = sum(1 for c in self.cards if c.is_verified())
        pend = total - ver
        pref = sum(1 for c in self.cards if c.priority == "Prefeituras")
        self.s_total.set_value(str(total))
        self.s_ver.set_value(str(ver))
        self.s_pend.set_value(str(pend))
        self.s_pref.set_value(str(pref))


# ══════════════════════════════════════════════════════════════════
#  SETTINGS DIALOG
# ══════════════════════════════════════════════════════════════════
class SettingsDialog(QDialog):
    def __init__(self, parent, db, ld):
        super().__init__(parent)
        self.db, self.ld = db, ld
        self.setWindowTitle("Configurações")
        self.setMinimumWidth(380)
        self.setStyleSheet(f"background:{C['surface']};")
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24,24,24,24); lay.setSpacing(12)
        lay.addWidget(QLabel("Informações da Licença",
            styleSheet=f"color:{C['accent2']};font-size:14px;font-weight:700;background:transparent;"))

        grid = QGridLayout()
        fields = [("Usuário", self.ld.get("user_name","—")),
                  ("Serial",  self.ld.get("serial","—")),
                  ("Validade",format_date_br(self.ld.get("valid_until","")))]
        for i,(k,v) in enumerate(fields):
            grid.addWidget(QLabel(k+":", styleSheet=f"color:{C['text3']};background:transparent;"), i,0)
            grid.addWidget(QLabel(v, styleSheet=f"color:{C['text']};font-weight:600;background:transparent;"), i,1)
        lay.addLayout(grid)

        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"background:{C['border']};"); sep.setFixedHeight(1)
        lay.addWidget(sep)

        imp = QPushButton("Importar Nova Licença")
        imp.clicked.connect(self._reimport); lay.addWidget(imp)

        clr = QPushButton("Limpar Licença")
        clr.setStyleSheet(f"color:{C['red']};border-color:{C['red']};")
        clr.clicked.connect(self._clear); lay.addWidget(clr)

        ok = QPushButton("Fechar"); ok.setObjectName("primary"); ok.clicked.connect(self.accept)
        lay.addWidget(ok)

    def _reimport(self):
        path,_ = QFileDialog.getOpenFileName(self,"Licença","","*.lic")
        if not path: return
        try:
            data = load_license_from_file(path)
            ok, msg = validate_license_data(data, get_mac_hash())
            if ok:
                self.db.save_license(data["serial"],data["user_name"],data["valid_until"],get_mac_hash())
                QMessageBox.information(self,"OK",f"Licença importada!\n{msg}")
                self.accept()
            else:
                QMessageBox.warning(self,"Inválida",msg)
        except Exception as e:
            QMessageBox.critical(self,"Erro",str(e))

    def _clear(self):
        r = QMessageBox.question(self,"Confirmar","Limpar licença?",QMessageBox.Yes|QMessageBox.No)
        if r == QMessageBox.Yes:
            self.db.clear_license(); QApplication.quit()


# ══════════════════════════════════════════════════════════════════
#  MAIN WINDOW — icon sidebar
# ══════════════════════════════════════════════════════════════════
class MainWindow(QWidget):
    def __init__(self, db, ld):
        super().__init__()
        self.db, self.ld = db, ld
        self._workers = []
        self._build()
        QTimer.singleShot(3000, self._check_update)

    def _build(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0,0,0,0); root.setSpacing(0)
        self.setStyleSheet(f"background:{C['bg']};")

        # ── ICON SIDEBAR ──────────────────────────────────────
        side = QWidget(); side.setFixedWidth(64)
        side.setStyleSheet(f"background:{C['sidebar']};border-right:1px solid {C['border']};")
        sl = QVBoxLayout(side)
        sl.setContentsMargins(0,18,0,18); sl.setSpacing(6)
        sl.setAlignment(Qt.AlignHCenter)

        logo = QLabel("⚖")
        logo.setFixedSize(34,34)
        logo.setAlignment(Qt.AlignCenter)
        logo.setStyleSheet(f"background:{C['accent']};color:#0B0C10;border-radius:10px;font-size:17px;font-weight:700;")
        sl.addWidget(logo)
        sl.addSpacing(14)

        nav_btn = QPushButton("▦")
        nav_btn.setObjectName("navicon"); nav_btn.setCheckable(True); nav_btn.setChecked(True)
        nav_btn.setFixedSize(38,38)
        nav_btn.setStyleSheet(nav_btn.styleSheet() + f"QPushButton{{color:{C['accent2']};font-size:16px;}}")
        sl.addWidget(nav_btn)

        sl.addStretch()

        user_name = self.ld.get("user_name","")
        initials = "".join([w[0] for w in user_name.split()[:2]]).upper() or "U"
        avatar = QLabel(initials)
        avatar.setFixedSize(34,34)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet(f"background:{C['green_bg']};color:{C['green']};border-radius:17px;font-size:12px;font-weight:600;")
        avatar.setToolTip(user_name)
        sl.addWidget(avatar)

        root.addWidget(side)

        # ── MAIN AREA ─────────────────────────────────────────
        main = QWidget(); main.setStyleSheet(f"background:{C['bg']};")
        ml = QVBoxLayout(main); ml.setContentsMargins(0,0,0,0); ml.setSpacing(0)

        self.editais_page = EditaisPage(self.db)
        self.editais_page._settings_btn.clicked.connect(self._settings)
        ml.addWidget(self.editais_page, 1)

        # Status footer
        stbar = QWidget(); stbar.setFixedHeight(28)
        stbar.setStyleSheet(f"background:{C['surface']};border-top:1px solid {C['border']};")
        stl = QHBoxLayout(stbar); stl.setContentsMargins(28,0,28,0)

        valid_until = self.ld.get("valid_until","")
        dr = days_remaining(valid_until)
        if dr < 0:   lic_t, lic_c = "Licença expirada", C["red"]
        elif dr <=7: lic_t, lic_c = f"Expira em {dr} dias", C["yellow"]
        else:        lic_t, lic_c = f"Licença válida até {format_date_br(valid_until)}", C["green"]
        lic_lbl = QLabel(lic_t)
        lic_lbl.setStyleSheet(f"color:{lic_c};font-size:11px;background:transparent;")
        stl.addWidget(lic_lbl)
        stl.addStretch()

        self.ver_lbl = QLabel(f"v{APP_VERSION}")
        self.ver_lbl.setStyleSheet(f"color:{C['text3']};font-size:11px;background:transparent;")
        stl.addWidget(self.ver_lbl)

        ml.addWidget(stbar)
        root.addWidget(main, 1)

    def _settings(self):
        SettingsDialog(self, self.db, self.ld).exec()

    def _check_update(self):
        base = GITHUB_URL.rsplit("/",1)[0]
        w = UpdateWorker(base+"/version.json")
        self._workers.append(w)
        w.found.connect(self._on_update)
        w.start()

    def _on_update(self, data):
        ver = data.get("version","?")
        r = QMessageBox.question(self,"Atualização Disponível",
            f"Nova versão {ver} disponível!\n\n{data.get('release_notes','')}\n\nAtualizar agora?",
            QMessageBox.Yes|QMessageBox.No)
        if r == QMessageBox.Yes:
            QDesktopServices.openUrl(QUrl(data.get("download_url","")))


# ══════════════════════════════════════════════════════════════════
#  APP ENTRY
# ══════════════════════════════════════════════════════════════════
class ClientApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Edital System")
        self.setMinimumSize(1040, 680)
        self.db = ClientDB()
        self._stk = QStackedWidget()
        self.setCentralWidget(self._stk)
        self._stk.setStyleSheet(f"background:{C['bg']};")
        self._check_license()

    def _check_license(self):
        lic = self.db.get_license()
        if not lic:
            self._show_activation(); return
        data = dict(lic)
        ok, msg = validate_license_data({
            "serial":data["serial_key"],"user_name":data["user_name"],
            "valid_until":data["valid_until"],"mac_hash":data["mac_hash"],
        }, get_mac_hash())
        if not ok:
            self.db.clear_license(); self._show_activation(msg); return
        if self._is_revoked(data["serial_key"]):
            self.db.clear_license()
            self._show_activation("Licença cancelada. Contate o administrador.")
            return
        self._show_main({"serial":data["serial_key"],"user_name":data["user_name"],
                         "valid_until":data["valid_until"]})

    def _is_revoked(self, serial):
        try:
            base = GITHUB_URL.rsplit("/",1)[0]
            with urllib.request.urlopen(base+"/blocked_serials.json", timeout=4) as r:
                return serial in json.loads(r.read().decode()).get("blocked",[])
        except Exception:
            return False

    def _show_activation(self, msg=""):
        ls = LicenseScreen(self.db, msg)
        ls.activation_success.connect(self._show_main)
        self._stk.addWidget(ls); self._stk.setCurrentWidget(ls)

    def _show_main(self, ld):
        if hasattr(self,"_mw"): return
        self._mw = MainWindow(self.db, ld)
        self._stk.addWidget(self._mw); self._stk.setCurrentWidget(self._mw)
        self.setWindowTitle(f"Edital System — {ld.get('user_name','')}")


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    pal = QPalette()
    pal.setColor(QPalette.Window, QColor(C["bg"]))
    pal.setColor(QPalette.WindowText, QColor(C["text"]))
    pal.setColor(QPalette.Base, QColor(C["surface"]))
    pal.setColor(QPalette.Text, QColor(C["text"]))
    pal.setColor(QPalette.Button, QColor(C["surface"]))
    pal.setColor(QPalette.ButtonText, QColor(C["text"]))
    pal.setColor(QPalette.Highlight, QColor(C["accent"]))
    pal.setColor(QPalette.HighlightedText, QColor("#0B0C10"))
    app.setPalette(pal)
    app.setStyleSheet(STYLE)
    win = ClientApp()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
