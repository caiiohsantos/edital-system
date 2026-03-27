# admin/painel_admin.py
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QDialog, QFormLayout, QMessageBox, QComboBox, QTextEdit,
    QStackedWidget, QFrame, QScrollArea, QHeaderView, QDateEdit,
    QFileDialog, QSpinBox, QTabWidget, QCheckBox, QSizePolicy,
    QGridLayout, QSplitter, QListWidget, QListWidgetItem,
)
from PySide6.QtCore import (
    Qt, QThread, Signal, QDate, QTimer, QSize,
)
from PySide6.QtGui import (
    QFont, QColor, QIcon, QPalette, QPixmap, QCursor,
)

from core.database import AdminDB
from core.utils import (
    generate_serial_key, format_date_br, format_datetime_br,
    days_remaining, is_expired, get_mac_hash,
)
from core.license_core import generate_license_file, save_license_file
from core.editals_data import EDITALS_DATA
import datetime

# ─────────────────────────────────────────────
#  THEME / STYLES
# ─────────────────────────────────────────────

DARK_STYLE = """
QMainWindow, QDialog, QWidget {
    background-color: #0d1117;
    color: #c9d1d9;
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
}
QLabel { color: #c9d1d9; }
QLabel#title { font-size: 22px; font-weight: bold; color: #58a6ff; }
QLabel#subtitle { font-size: 13px; color: #8b949e; }
QLabel#section { font-size: 15px; font-weight: bold; color: #e6edf3;
                  padding: 4px 0; border-bottom: 1px solid #30363d; }
QLabel#stat_value { font-size: 32px; font-weight: bold; color: #58a6ff; }
QLabel#stat_label { font-size: 12px; color: #8b949e; }

QLineEdit, QTextEdit, QComboBox, QSpinBox, QDateEdit {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 6px 10px;
    color: #c9d1d9;
    selection-background-color: #58a6ff;
}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus,
QSpinBox:focus, QDateEdit:focus {
    border-color: #58a6ff;
}
QComboBox::drop-down { border: none; }
QComboBox::down-arrow { image: none; }
QComboBox QAbstractItemView {
    background-color: #161b22;
    border: 1px solid #30363d;
    selection-background-color: #21262d;
    color: #c9d1d9;
}

QPushButton {
    background-color: #21262d;
    color: #c9d1d9;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 7px 16px;
    font-weight: 500;
}
QPushButton:hover { background-color: #30363d; border-color: #58a6ff; }
QPushButton:pressed { background-color: #161b22; }
QPushButton#primary {
    background-color: #1f6feb;
    color: white;
    border: none;
}
QPushButton#primary:hover { background-color: #388bfd; }
QPushButton#danger {
    background-color: #da3633;
    color: white;
    border: none;
}
QPushButton#danger:hover { background-color: #f85149; }
QPushButton#success {
    background-color: #238636;
    color: white;
    border: none;
}
QPushButton#success:hover { background-color: #2ea043; }
QPushButton#warning {
    background-color: #9e6a03;
    color: white;
    border: none;
}
QPushButton#warning:hover { background-color: #d29922; }

QTableWidget {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 6px;
    gridline-color: #21262d;
    color: #c9d1d9;
    selection-background-color: #1f6feb;
}
QTableWidget::item { padding: 6px 8px; }
QTableWidget::item:selected { background-color: #1f6feb; }
QHeaderView::section {
    background-color: #21262d;
    color: #8b949e;
    border: none;
    border-bottom: 1px solid #30363d;
    padding: 8px;
    font-weight: 600;
    font-size: 12px;
    text-transform: uppercase;
}

QFrame#card {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 16px;
}
QFrame#sidebar {
    background-color: #161b22;
    border-right: 1px solid #30363d;
}
QListWidget {
    background-color: #161b22;
    border: none;
    outline: none;
}
QListWidget::item {
    color: #8b949e;
    border-radius: 6px;
    padding: 10px 16px;
    margin: 2px 8px;
}
QListWidget::item:hover { background-color: #21262d; color: #c9d1d9; }
QListWidget::item:selected {
    background-color: #1f6feb22;
    color: #58a6ff;
    border-left: 3px solid #58a6ff;
}
QScrollBar:vertical {
    background: #0d1117;
    width: 8px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #30363d;
    border-radius: 4px;
    min-height: 20px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QTabWidget::pane { border: 1px solid #30363d; background: #161b22; }
QTabBar::tab {
    background: #161b22;
    color: #8b949e;
    padding: 8px 20px;
    border: 1px solid #30363d;
    border-bottom: none;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}
QTabBar::tab:selected { background: #21262d; color: #58a6ff; border-color: #30363d; }
"""


# ─────────────────────────────────────────────
#  WORKER THREAD
# ─────────────────────────────────────────────

class Worker(QThread):
    result = Signal(object)
    error = Signal(str)

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self._fn = fn
        self._args = args
        self._kwargs = kwargs

    def run(self):
        try:
            self.result.emit(self._fn(*self._args, **self._kwargs))
        except Exception as e:
            self.error.emit(str(e))


# ─────────────────────────────────────────────
#  LOGIN SCREEN
# ─────────────────────────────────────────────

class LoginScreen(QWidget):
    login_success = Signal()

    def __init__(self, db: AdminDB):
        super().__init__()
        self.db = db
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        # Card container
        card = QFrame()
        card.setObjectName("card")
        card.setFixedWidth(400)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(16)
        card_layout.setContentsMargins(32, 32, 32, 32)

        logo = QLabel("🚦")
        logo.setAlignment(Qt.AlignCenter)
        logo.setFont(QFont("Segoe UI", 40))
        card_layout.addWidget(logo)

        title = QLabel("Edital System")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(title)

        sub = QLabel("Painel Administrativo")
        sub.setObjectName("subtitle")
        sub.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(sub)

        card_layout.addSpacing(16)

        self.pw_input = QLineEdit()
        self.pw_input.setPlaceholderText("Senha de administrador")
        self.pw_input.setEchoMode(QLineEdit.Password)
        self.pw_input.setFixedHeight(42)
        self.pw_input.returnPressed.connect(self._do_login)
        card_layout.addWidget(self.pw_input)

        btn = QPushButton("Entrar")
        btn.setObjectName("primary")
        btn.setFixedHeight(42)
        btn.clicked.connect(self._do_login)
        card_layout.addWidget(btn)

        self.msg = QLabel("")
        self.msg.setAlignment(Qt.AlignCenter)
        self.msg.setStyleSheet("color: #f85149;")
        card_layout.addWidget(self.msg)

        layout.addWidget(card)

    def _do_login(self):
        pw = self.pw_input.text()
        if self.db.verify_admin(pw):
            self.login_success.emit()
        else:
            self.msg.setText("Senha incorreta.")
            self.pw_input.clear()


# ─────────────────────────────────────────────
#  STAT CARD WIDGET
# ─────────────────────────────────────────────

class StatCard(QFrame):
    def __init__(self, label: str, value: str, color: str = "#58a6ff"):
        super().__init__()
        self.setObjectName("card")
        self.setFixedHeight(110)
        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignCenter)

        vl = QLabel(value)
        vl.setObjectName("stat_value")
        vl.setStyleSheet(f"color: {color}; font-size: 32px; font-weight: bold;")
        vl.setAlignment(Qt.AlignCenter)
        lay.addWidget(vl)
        self._vl = vl

        lb = QLabel(label)
        lb.setObjectName("stat_label")
        lb.setAlignment(Qt.AlignCenter)
        lay.addWidget(lb)

    def set_value(self, v: str):
        self._vl.setText(v)


# ─────────────────────────────────────────────
#  DASHBOARD PAGE
# ─────────────────────────────────────────────

class DashboardPage(QWidget):
    def __init__(self, db: AdminDB):
        super().__init__()
        self.db = db
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        hdr = QLabel("Dashboard")
        hdr.setObjectName("title")
        layout.addWidget(hdr)

        # Stats row
        self.stat_total  = StatCard("Total de Usuários", "—")
        self.stat_active  = StatCard("Licenças Ativas", "—", "#2ea043")
        self.stat_expire  = StatCard("Vencem em 7 dias", "—", "#d29922")
        self.stat_expired = StatCard("Expiradas", "—", "#f85149")

        stats_row = QHBoxLayout()
        for w in [self.stat_total, self.stat_active, self.stat_expire, self.stat_expired]:
            stats_row.addWidget(w)
        layout.addLayout(stats_row)

        # Recent users
        sec = QLabel("Usuários Recentes")
        sec.setObjectName("section")
        layout.addWidget(sec)

        self.recent_table = self._make_table(
            ["Nome", "Email", "Válido até", "Status"]
        )
        layout.addWidget(self.recent_table)
        layout.addStretch()
        self.refresh()

    def _make_table(self, headers):
        t = QTableWidget(0, len(headers))
        t.setHorizontalHeaderLabels(headers)
        t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        t.setEditTriggers(QTableWidget.NoEditTriggers)
        t.setSelectionBehavior(QTableWidget.SelectRows)
        t.verticalHeader().setVisible(False)
        return t

    def refresh(self):
        stats = self.db.get_stats()
        self.stat_total.set_value(str(stats["total"]))
        self.stat_active.set_value(str(stats["active"]))
        self.stat_expire.set_value(str(stats["expiring_soon"]))
        self.stat_expired.set_value(str(stats["expired"]))

        users = self.db.get_all_users()
        self.recent_table.setRowCount(0)
        for u in users[:10]:
            r = self.recent_table.rowCount()
            self.recent_table.insertRow(r)
            exp = is_expired(u["valid_until"])
            status = "❌ Expirada" if exp else ("✅ Ativa" if u["is_active"] else "🚫 Bloqueada")
            self.recent_table.setItem(r, 0, QTableWidgetItem(u["nome"]))
            self.recent_table.setItem(r, 1, QTableWidgetItem(u["email"] or "—"))
            self.recent_table.setItem(r, 2, QTableWidgetItem(format_date_br(u["valid_until"])))
            self.recent_table.setItem(r, 3, QTableWidgetItem(status))


# ─────────────────────────────────────────────
#  USER DIALOG (Create / Edit)
# ─────────────────────────────────────────────

class UserDialog(QDialog):
    def __init__(self, parent, db: AdminDB, user=None):
        super().__init__(parent)
        self.db = db
        self.user = user
        self.setWindowTitle("Novo Usuário" if not user else "Editar Usuário")
        self.setMinimumWidth(440)
        self._build()
        if user:
            self._load()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)

        form = QFormLayout()
        form.setSpacing(10)

        self.nome = QLineEdit()
        self.nome.setPlaceholderText("Nome completo")
        form.addRow("Nome *", self.nome)

        self.email = QLineEdit()
        self.email.setPlaceholderText("email@exemplo.com")
        form.addRow("E-mail", self.email)

        self.days = QSpinBox()
        self.days.setRange(1, 3650)
        self.days.setValue(30)
        self.days.setSuffix(" dias")
        form.addRow("Validade", self.days)

        self.serial = QLineEdit()
        self.serial.setReadOnly(True)
        serial_row = QHBoxLayout()
        serial_row.addWidget(self.serial)
        gen_btn = QPushButton("Gerar")
        gen_btn.setObjectName("primary")
        gen_btn.clicked.connect(self._gen_serial)
        serial_row.addWidget(gen_btn)
        form.addRow("Serial Key", serial_row)

        self.notes = QTextEdit()
        self.notes.setFixedHeight(70)
        self.notes.setPlaceholderText("Observações...")
        form.addRow("Notas", self.notes)

        layout.addLayout(form)

        # Buttons
        btn_row = QHBoxLayout()
        cancel = QPushButton("Cancelar")
        cancel.clicked.connect(self.reject)
        save = QPushButton("Salvar")
        save.setObjectName("primary")
        save.clicked.connect(self._save)
        btn_row.addWidget(cancel)
        btn_row.addStretch()
        btn_row.addWidget(save)
        layout.addLayout(btn_row)

    def _gen_serial(self):
        self.serial.setText(generate_serial_key())

    def _load(self):
        u = self.user
        self.nome.setText(u["nome"])
        self.email.setText(u["email"] or "")
        self.serial.setText(u["serial_key"])
        dr = days_remaining(u["valid_until"])
        self.days.setValue(max(1, dr))
        self.notes.setPlainText(u["notes"] or "")

    def _save(self):
        nome = self.nome.text().strip()
        if not nome:
            QMessageBox.warning(self, "Atenção", "Nome é obrigatório.")
            return
        serial = self.serial.text().strip()
        if not serial:
            QMessageBox.warning(self, "Atenção", "Gere um serial key.")
            return

        if self.user:
            new_valid = (datetime.datetime.now() +
                         datetime.timedelta(days=self.days.value())).strftime("%Y-%m-%d")
            self.db.update_user(
                self.user["id"], nome, self.email.text().strip(),
                new_valid, self.user["is_active"], self.notes.toPlainText()
            )
        else:
            self.db.create_user(
                nome, self.email.text().strip(), serial,
                self.days.value(), self.notes.toPlainText()
            )
        self.accept()


# ─────────────────────────────────────────────
#  USERS PAGE
# ─────────────────────────────────────────────

class UsersPage(QWidget):
    def __init__(self, db: AdminDB):
        super().__init__()
        self.db = db
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header row
        hdr = QHBoxLayout()
        title = QLabel("Gestão de Usuários")
        title.setObjectName("title")
        hdr.addWidget(title)
        hdr.addStretch()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍  Buscar usuário...")
        self.search_input.setFixedWidth(220)
        self.search_input.textChanged.connect(self.refresh)
        hdr.addWidget(self.search_input)

        new_btn = QPushButton("+ Novo Usuário")
        new_btn.setObjectName("primary")
        new_btn.clicked.connect(self._new_user)
        hdr.addWidget(new_btn)
        layout.addLayout(hdr)

        # Table
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels([
            "ID", "Nome", "E-mail", "Serial Key",
            "Válido até", "MAC", "Status", "Ações"
        ])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(
            "QTableWidget { alternate-background-color: #0d1117; }"
        )
        layout.addWidget(self.table)
        self.refresh()

    def refresh(self):
        search = self.search_input.text().lower()
        users = self.db.get_all_users()
        self.table.setRowCount(0)
        for u in users:
            if search and search not in u["nome"].lower() and search not in (u["email"] or "").lower():
                continue
            r = self.table.rowCount()
            self.table.insertRow(r)

            exp = is_expired(u["valid_until"])
            active = u["is_active"]
            if exp:
                status = "❌ Expirada"
                sc = "#f85149"
            elif not active:
                status = "🚫 Bloqueada"
                sc = "#d29922"
            else:
                dr = days_remaining(u["valid_until"])
                status = f"✅ Ativa ({dr}d)"
                sc = "#2ea043"

            self.table.setItem(r, 0, QTableWidgetItem(str(u["id"])))
            self.table.setItem(r, 1, QTableWidgetItem(u["nome"]))
            self.table.setItem(r, 2, QTableWidgetItem(u["email"] or "—"))
            ki = QTableWidgetItem(u["serial_key"])
            ki.setForeground(QColor("#58a6ff"))
            self.table.setItem(r, 3, ki)
            self.table.setItem(r, 4, QTableWidgetItem(format_date_br(u["valid_until"])))
            mac_val = "✓ Vinculado" if u["mac_hash"] else "—"
            self.table.setItem(r, 5, QTableWidgetItem(mac_val))
            si = QTableWidgetItem(status)
            si.setForeground(QColor(sc))
            self.table.setItem(r, 6, si)

            # Action buttons
            action_w = QWidget()
            action_l = QHBoxLayout(action_w)
            action_l.setContentsMargins(4, 2, 4, 2)
            action_l.setSpacing(4)

            edit_btn = QPushButton("✏️")
            edit_btn.setFixedSize(28, 28)
            edit_btn.setToolTip("Editar")
            edit_btn.clicked.connect(lambda _, uid=u["id"]: self._edit_user(uid))

            toggle_btn = QPushButton("🚫" if active else "✅")
            toggle_btn.setFixedSize(28, 28)
            toggle_btn.setToolTip("Bloquear/Ativar")
            toggle_btn.clicked.connect(lambda _, uid=u["id"]: self._toggle(uid))

            renew_btn = QPushButton("🔄")
            renew_btn.setFixedSize(28, 28)
            renew_btn.setToolTip("Renovar 30 dias")
            renew_btn.clicked.connect(lambda _, uid=u["id"]: self._renew(uid))

            lic_btn = QPushButton("📄")
            lic_btn.setFixedSize(28, 28)
            lic_btn.setToolTip("Exportar Licença (.lic)")
            lic_btn.clicked.connect(lambda _, uid=u["id"]: self._export_lic(uid))

            del_btn = QPushButton("🗑️")
            del_btn.setFixedSize(28, 28)
            del_btn.setToolTip("Excluir")
            del_btn.clicked.connect(lambda _, uid=u["id"]: self._delete(uid))

            for b in [edit_btn, toggle_btn, renew_btn, lic_btn, del_btn]:
                b.setStyleSheet("font-size: 14px; padding: 0;")
                action_l.addWidget(b)
            action_l.addStretch()

            self.table.setCellWidget(r, 7, action_w)
            self.table.setRowHeight(r, 44)

    def _new_user(self):
        d = UserDialog(self, self.db)
        if d.exec():
            self.refresh()

    def _edit_user(self, uid: int):
        users = self.db.get_all_users()
        u = next((x for x in users if x["id"] == uid), None)
        if u:
            d = UserDialog(self, self.db, u)
            if d.exec():
                self.refresh()

    def _toggle(self, uid: int):
        self.db.toggle_user_active(uid)
        self.refresh()

    def _renew(self, uid: int):
        days, ok = self._ask_days()
        if ok:
            self.db.renew_user(uid, days)
            self.refresh()

    def _ask_days(self):
        from PySide6.QtWidgets import QInputDialog
        val, ok = QInputDialog.getInt(
            self, "Renovar", "Quantos dias?", 30, 1, 3650
        )
        return val, ok

    def _export_lic(self, uid: int):
        users = self.db.get_all_users()
        u = next((x for x in users if x["id"] == uid), None)
        if not u:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Salvar Licença", f"{u['nome'].replace(' ','_')}_license.lic",
            "Arquivo de Licença (*.lic)"
        )
        if path:
            content = generate_license_file(
                u["serial_key"], u["nome"],
                u["valid_until"], u["mac_hash"] or ""
            )
            with open(path, "wb") as f:
                f.write(content)
            QMessageBox.information(self, "Sucesso",
                f"Arquivo de licença exportado para:\n{path}")

    def _delete(self, uid: int):
        reply = QMessageBox.question(
            self, "Confirmar", "Excluir este usuário permanentemente?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.db.delete_user(uid)
            self.refresh()


# ─────────────────────────────────────────────
#  EDITAIS PAGE
# ─────────────────────────────────────────────

class EditaisPage(QWidget):
    def __init__(self, db: AdminDB):
        super().__init__()
        self.db = db
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Configuração de Tutoriais")
        title.setObjectName("title")
        layout.addWidget(title)

        sub = QLabel("Defina o link do YouTube para o tutorial de cada edital. "
                     "Deixe em branco para desativar.")
        sub.setObjectName("subtitle")
        sub.setWordWrap(True)
        layout.addWidget(sub)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(
            ["Prioridade", "Edital", "URL do Tutorial", "Ação"]
        )
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)
        self._load()

    def _load(self):
        self.table.setRowCount(0)
        config = self.db.get_all_editals_config()

        priority_colors = {
            "Prioridade 1": "#e94560",
            "Prioridade 2": "#f5a623",
            "Prioridade 3": "#4a9eff",
            "Prioridade 4": "#8b949e",
        }

        for prio, editals in EDITALS_DATA.items():
            for e in editals:
                r = self.table.rowCount()
                self.table.insertRow(r)

                pi = QTableWidgetItem(prio)
                pi.setForeground(QColor(priority_colors.get(prio, "#c9d1d9")))
                self.table.setItem(r, 0, pi)
                self.table.setItem(r, 1, QTableWidgetItem(e["nome"]))

                tut_url = config.get(e["id"], e.get("tutorial_url", ""))
                url_item = QTableWidgetItem(tut_url or "—")
                url_item.setForeground(QColor("#8b949e") if not tut_url else QColor("#58a6ff"))
                self.table.setItem(r, 2, url_item)

                edit_btn = QPushButton("✏️ Editar")
                edit_btn.setFixedHeight(28)
                edit_btn.clicked.connect(
                    lambda _, eid=e["id"], ename=e["nome"], eu=tut_url:
                    self._edit_tutorial(eid, ename, eu)
                )
                self.table.setCellWidget(r, 3, edit_btn)
                self.table.setRowHeight(r, 40)

    def _edit_tutorial(self, edital_id: str, nome: str, current_url: str):
        d = QDialog(self)
        d.setWindowTitle(f"Tutorial — {nome}")
        d.setMinimumWidth(500)
        lay = QVBoxLayout(d)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(12)

        lay.addWidget(QLabel(f"<b>{nome}</b>"))
        note = QLabel("Cole o link do YouTube (ex: https://youtu.be/XXXXXXXXXXX)")
        note.setObjectName("subtitle")
        lay.addWidget(note)

        url_input = QLineEdit(current_url)
        url_input.setPlaceholderText("https://www.youtube.com/watch?v=...")
        lay.addWidget(url_input)

        btn_row = QHBoxLayout()
        cancel = QPushButton("Cancelar")
        cancel.clicked.connect(d.reject)
        save = QPushButton("Salvar")
        save.setObjectName("primary")

        def _save():
            url = url_input.text().strip()
            self.db.set_tutorial_url(edital_id, url)

            # Exportar tutorials.json compartilhado para o cliente ler
            from core.tutorials_sync import save_tutorials
            all_tutorials = self.db.get_all_editals_config()
            ok = save_tutorials(all_tutorials)

            d.accept()
            self._load()

            if ok:
                QMessageBox.information(
                    self, "Salvo",
                    "Tutorial salvo!\n\n"
                    "O cliente vai carregar automaticamente\n"
                    "ao reabrir o app."
                )
            else:
                QMessageBox.warning(
                    self, "Atencao",
                    "Tutorial salvo no banco, mas nao foi possivel\n"
                    "exportar o tutorials.json.\n\n"
                    "Verifique permissoes de escrita na pasta do projeto."
                )

        save.clicked.connect(_save)
        btn_row.addWidget(cancel)
        btn_row.addStretch()
        btn_row.addWidget(save)
        lay.addLayout(btn_row)
        d.exec()


# ─────────────────────────────────────────────
#  SETTINGS PAGE
# ─────────────────────────────────────────────

class SettingsPage(QWidget):
    def __init__(self, db: AdminDB):
        super().__init__()
        self.db = db
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        layout.addWidget(QLabel("Configurações", objectName="title"))

        # App version
        sec1 = QLabel("Versão do Aplicativo (para auto-update)")
        sec1.setObjectName("section")
        layout.addWidget(sec1)

        ver_row = QHBoxLayout()
        self.ver_input = QLineEdit(self.db.get_setting("app_version", "1.0.0"))
        self.ver_input.setFixedWidth(140)
        ver_row.addWidget(QLabel("Versão atual:"))
        ver_row.addWidget(self.ver_input)
        ver_row.addStretch()
        layout.addLayout(ver_row)

        url_row = QHBoxLayout()
        self.update_url = QLineEdit(self.db.get_setting("update_url", ""))
        self.update_url.setPlaceholderText("https://exemplo.com/version.json")
        url_row.addWidget(QLabel("URL de atualização:"))
        url_row.addWidget(self.update_url)
        layout.addLayout(url_row)

        save_ver_btn = QPushButton("Salvar configurações de versão")
        save_ver_btn.setObjectName("primary")
        save_ver_btn.clicked.connect(self._save_version)
        layout.addWidget(save_ver_btn)

        # Password change
        sec2 = QLabel("Alterar Senha do Administrador")
        sec2.setObjectName("section")
        layout.addWidget(sec2)

        form = QFormLayout()
        self.old_pw = QLineEdit()
        self.old_pw.setEchoMode(QLineEdit.Password)
        self.new_pw = QLineEdit()
        self.new_pw.setEchoMode(QLineEdit.Password)
        self.confirm_pw = QLineEdit()
        self.confirm_pw.setEchoMode(QLineEdit.Password)
        form.addRow("Senha atual:", self.old_pw)
        form.addRow("Nova senha:", self.new_pw)
        form.addRow("Confirmar:", self.confirm_pw)
        layout.addLayout(form)

        ch_btn = QPushButton("Alterar Senha")
        ch_btn.setObjectName("warning")
        ch_btn.clicked.connect(self._change_pw)
        layout.addWidget(ch_btn)

        layout.addStretch()

    def _save_version(self):
        self.db.set_setting("app_version", self.ver_input.text().strip())
        self.db.set_setting("update_url", self.update_url.text().strip())
        QMessageBox.information(self, "Salvo", "Configurações salvas com sucesso.")

    def _change_pw(self):
        old = self.old_pw.text()
        new = self.new_pw.text()
        conf = self.confirm_pw.text()
        if not self.db.verify_admin(old):
            QMessageBox.warning(self, "Erro", "Senha atual incorreta.")
            return
        if new != conf:
            QMessageBox.warning(self, "Erro", "As senhas não coincidem.")
            return
        if len(new) < 6:
            QMessageBox.warning(self, "Erro", "A senha deve ter pelo menos 6 caracteres.")
            return
        self.db.change_admin_password(new)
        QMessageBox.information(self, "Sucesso", "Senha alterada com sucesso.")
        self.old_pw.clear(); self.new_pw.clear(); self.confirm_pw.clear()


# ─────────────────────────────────────────────
#  MAIN ADMIN WINDOW
# ─────────────────────────────────────────────

class AdminMainWindow(QWidget):
    def __init__(self, db: AdminDB):
        super().__init__()
        self.db = db
        self._build()

    def _build(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(0, 0, 0, 0)
        sb_layout.setSpacing(0)

        # Logo
        logo_w = QWidget()
        logo_w.setFixedHeight(70)
        logo_l = QHBoxLayout(logo_w)
        logo_l.setContentsMargins(16, 12, 16, 12)
        icon_lbl = QLabel("🚦")
        icon_lbl.setFont(QFont("Segoe UI", 22))
        name_lbl = QLabel("Edital\nSystem")
        name_lbl.setStyleSheet("color: #58a6ff; font-weight: bold; font-size: 13px;")
        logo_l.addWidget(icon_lbl)
        logo_l.addWidget(name_lbl)
        logo_l.addStretch()
        sb_layout.addWidget(logo_w)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background: #30363d;")
        sep.setFixedHeight(1)
        sb_layout.addWidget(sep)

        # Nav
        self.nav = QListWidget()
        self.nav.setSpacing(2)
        items = [
            ("📊  Dashboard", 0),
            ("👥  Usuários", 1),
            ("📋  Editais / Tutoriais", 2),
            ("⚙️  Configurações", 3),
        ]
        for label, idx in items:
            item = QListWidgetItem(label)
            item.setSizeHint(QSize(200, 44))
            self.nav.addItem(item)
        self.nav.setCurrentRow(0)
        self.nav.currentRowChanged.connect(self._switch_page)
        sb_layout.addWidget(self.nav)
        sb_layout.addStretch()

        # Version label
        ver_lbl = QLabel("v1.0.0 — Admin")
        ver_lbl.setStyleSheet("color: #30363d; font-size: 11px; padding: 12px;")
        sb_layout.addWidget(ver_lbl)

        main_layout.addWidget(sidebar)

        # Content area
        self.stack = QStackedWidget()
        self.dash_page = DashboardPage(self.db)
        self.users_page = UsersPage(self.db)
        self.editais_page = EditaisPage(self.db)
        self.settings_page = SettingsPage(self.db)

        for p in [self.dash_page, self.users_page, self.editais_page, self.settings_page]:
            self.stack.addWidget(p)

        main_layout.addWidget(self.stack)

    def _switch_page(self, idx: int):
        self.stack.setCurrentIndex(idx)
        if idx == 0:
            self.dash_page.refresh()
        elif idx == 1:
            self.users_page.refresh()


# ─────────────────────────────────────────────
#  APPLICATION ENTRY
# ─────────────────────────────────────────────

class AdminApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Edital System — Painel Admin")
        self.setMinimumSize(1200, 720)
        self.db = AdminDB()

        self._container = QStackedWidget()
        self.setCentralWidget(self._container)

        self.login_screen = LoginScreen(self.db)
        self.login_screen.login_success.connect(self._on_login)
        self._container.addWidget(self.login_screen)

        self.main_screen = AdminMainWindow(self.db)
        self._container.addWidget(self.main_screen)

    def _on_login(self):
        self._container.setCurrentWidget(self.main_screen)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#0d1117"))
    palette.setColor(QPalette.WindowText, QColor("#c9d1d9"))
    palette.setColor(QPalette.Base, QColor("#161b22"))
    palette.setColor(QPalette.AlternateBase, QColor("#0d1117"))
    palette.setColor(QPalette.Text, QColor("#c9d1d9"))
    palette.setColor(QPalette.Button, QColor("#21262d"))
    palette.setColor(QPalette.ButtonText, QColor("#c9d1d9"))
    palette.setColor(QPalette.Highlight, QColor("#1f6feb"))
    palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    app.setPalette(palette)
    app.setStyleSheet(DARK_STYLE)

    win = AdminApp()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
