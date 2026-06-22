# admin/painel_admin.py
import sys, os, datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QDialog, QFormLayout, QMessageBox, QTextEdit, QStackedWidget,
    QFrame, QHeaderView, QFileDialog, QSpinBox, QListWidget,
    QListWidgetItem, QGridLayout, QButtonGroup, QComboBox,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor, QPalette

from core.database import AdminDB
from core.utils import generate_serial_key, format_date_br, days_remaining, is_expired
from core.license_core import generate_license_file
from core.editals_data import EDITALS_DATA

C = {
    "bg":"#0B0C10","sidebar":"#0B0C10","surface":"#15171D","surface2":"#1B1E26",
    "border":"#232530","border2":"#2D303D","text":"#F2F2F0","text2":"#9094A0",
    "text3":"#6B6C76","accent":"#7F77DD","accent2":"#9A93E8","green":"#5DCAA5",
    "red":"#E9776F","yellow":"#EF9F27",
}

STYLE = f"""
* {{ font-family:'Segoe UI',sans-serif; }}
QMainWindow,QDialog,QWidget {{ background:{C['bg']};color:{C['text']};font-size:13px; }}
QWidget {{ background:transparent;color:{C['text']}; }}
QLineEdit,QTextEdit,QSpinBox,QComboBox {{
    background:{C['surface']};border:1px solid {C['border']};border-radius:7px;
    padding:7px 12px;color:{C['text']};
}}
QLineEdit:focus,QTextEdit:focus {{ border-color:{C['accent']}; }}
QPushButton {{
    background:{C['surface']};color:{C['text2']};border:1px solid {C['border']};
    border-radius:7px;padding:6px 14px;font-size:12px;font-weight:500;
}}
QPushButton:hover {{ background:{C['surface2']};color:{C['text']};border-color:{C['border2']}; }}
QPushButton#primary {{ background:{C['accent']};color:#0B0C10;border:none;border-radius:7px;padding:8px 20px;font-weight:600; }}
QPushButton#primary:hover {{ background:{C['accent2']}; }}
QPushButton#danger {{ background:{C['red']};color:white;border:none;border-radius:7px; }}
QPushButton#warning {{ background:{C['yellow']};color:white;border:none;border-radius:7px; }}
QPushButton#nav_btn {{ background:transparent;color:{C['text3']};border:none;border-radius:8px;padding:10px 14px;text-align:left;font-size:13px; }}
QPushButton#nav_btn:hover {{ background:{C['surface']};color:{C['text2']}; }}
QPushButton#nav_btn:checked {{ background:{C['surface2']};color:{C['text']};border-left:3px solid {C['accent']}; }}
QTableWidget {{ background:{C['surface']};border:1px solid {C['border']};border-radius:8px;gridline-color:{C['border']};color:{C['text']}; }}
QTableWidget::item {{ padding:6px 8px;border:none; }}
QHeaderView::section {{ background:{C['surface2']};color:{C['text3']};border:none;border-bottom:1px solid {C['border']};padding:8px;font-weight:700;font-size:11px; }}
QScrollBar:vertical {{ background:{C['bg']};width:5px;border-radius:3px; }}
QScrollBar::handle:vertical {{ background:{C['border2']};border-radius:3px;min-height:20px; }}
"""

class LoginScreen(QWidget):
    success = Signal()
    def __init__(self, db):
        super().__init__(); self.db = db; self._build()
    def _build(self):
        lay = QVBoxLayout(self); lay.setAlignment(Qt.AlignCenter)
        card = QWidget(); card.setFixedWidth(380)
        card.setStyleSheet(f"background:{C['surface']};border-radius:14px;border:1px solid {C['border']};")
        cl = QVBoxLayout(card); cl.setContentsMargins(36,36,36,36); cl.setSpacing(14)
        logo = QLabel("⚖ Edital System"); logo.setAlignment(Qt.AlignCenter)
        logo.setStyleSheet(f"font-size:20px;font-weight:700;color:{C['text']};background:transparent;")
        cl.addWidget(logo)
        sub = QLabel("Painel Administrativo"); sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet(f"font-size:12px;color:{C['text3']};background:transparent;")
        cl.addWidget(sub)
        self.pw = QLineEdit(); self.pw.setPlaceholderText("Senha")
        self.pw.setEchoMode(QLineEdit.Password); self.pw.setFixedHeight(38)
        self.pw.returnPressed.connect(self._login)
        cl.addWidget(self.pw)
        btn = QPushButton("Entrar"); btn.setObjectName("primary"); btn.setFixedHeight(38)
        btn.clicked.connect(self._login); cl.addWidget(btn)
        self.msg = QLabel(""); self.msg.setAlignment(Qt.AlignCenter)
        self.msg.setStyleSheet(f"color:{C['red']};font-size:12px;background:transparent;")
        cl.addWidget(self.msg)
        lay.addWidget(card)
    def _login(self):
        if self.db.verify_admin(self.pw.text()): self.success.emit()
        else: self.msg.setText("Senha incorreta."); self.pw.clear()


class StatCard(QFrame):
    def __init__(self, label, value, color):
        super().__init__()
        self.setStyleSheet(f"background:{C['surface']};border:1px solid {C['border']};border-radius:10px;border-top:3px solid {color};")
        lay = QVBoxLayout(self); lay.setAlignment(Qt.AlignCenter)
        self._val = QLabel(value); self._val.setAlignment(Qt.AlignCenter)
        self._val.setStyleSheet(f"color:{color};font-size:28px;font-weight:700;background:transparent;")
        lay.addWidget(self._val)
        lbl = QLabel(label); lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet(f"color:{C['text3']};font-size:11px;background:transparent;")
        lay.addWidget(lbl)
    def set_value(self, v): self._val.setText(v)


class DashboardPage(QWidget):
    def __init__(self, db):
        super().__init__(); self.db = db; self._build()
    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(24,24,24,24); lay.setSpacing(20)
        title = QLabel("Dashboard")
        title.setStyleSheet(f"font-size:22px;font-weight:700;color:{C['text']};background:transparent;")
        lay.addWidget(title)
        row = QHBoxLayout()
        self.s_total = StatCard("Total","—",C["accent"])
        self.s_active = StatCard("Ativas","—",C["green"])
        self.s_expire = StatCard("Vencem 7d","—",C["yellow"])
        self.s_expired = StatCard("Expiradas","—",C["red"])
        for w in [self.s_total,self.s_active,self.s_expire,self.s_expired]: row.addWidget(w)
        lay.addLayout(row)
        self.table = QTableWidget(0,4)
        self.table.setHorizontalHeaderLabels(["Nome","E-mail","Válido até","Status"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        lay.addWidget(self.table)
        self.refresh()
    def refresh(self):
        s = self.db.get_stats()
        self.s_total.set_value(str(s["total"])); self.s_active.set_value(str(s["active"]))
        self.s_expire.set_value(str(s["expiring_soon"])); self.s_expired.set_value(str(s["expired"]))
        users = self.db.get_all_users(); self.table.setRowCount(0)
        for u in users[:10]:
            r = self.table.rowCount(); self.table.insertRow(r)
            exp = is_expired(u["valid_until"])
            status = "Expirada" if exp else ("Ativa" if u["is_active"] else "Bloqueada")
            self.table.setItem(r,0,QTableWidgetItem(u["nome"]))
            self.table.setItem(r,1,QTableWidgetItem(u["email"] or "—"))
            self.table.setItem(r,2,QTableWidgetItem(format_date_br(u["valid_until"])))
            self.table.setItem(r,3,QTableWidgetItem(status))


class UserDialog(QDialog):
    def __init__(self, parent, db, user=None):
        super().__init__(parent); self.db=db; self.user=user
        self.setWindowTitle("Usuário"); self.setMinimumWidth(420)
        self.setStyleSheet(f"background:{C['surface']};")
        self._build()
        if user: self._load()
    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(20,20,20,20); lay.setSpacing(12)
        form = QFormLayout()
        self.nome = QLineEdit(); form.addRow("Nome",self.nome)
        self.email = QLineEdit(); form.addRow("E-mail",self.email)
        self.days = QSpinBox(); self.days.setRange(1,3650); self.days.setValue(30)
        form.addRow("Dias",self.days)
        self.serial = QLineEdit(); self.serial.setReadOnly(True)
        sr = QHBoxLayout(); sr.addWidget(self.serial)
        gb = QPushButton("Gerar"); gb.clicked.connect(lambda: self.serial.setText(generate_serial_key()))
        sr.addWidget(gb); form.addRow("Serial",sr)
        lay.addLayout(form)
        btns = QHBoxLayout()
        cancel = QPushButton("Cancelar"); cancel.clicked.connect(self.reject)
        save = QPushButton("Salvar"); save.setObjectName("primary"); save.clicked.connect(self._save)
        btns.addWidget(cancel); btns.addStretch(); btns.addWidget(save)
        lay.addLayout(btns)
    def _load(self):
        u = self.user
        self.nome.setText(u["nome"]); self.email.setText(u["email"] or "")
        self.serial.setText(u["serial_key"]); self.days.setValue(max(1,days_remaining(u["valid_until"])))
    def _save(self):
        if not self.nome.text().strip(): return
        if not self.serial.text().strip(): return
        if self.user:
            new_valid = (datetime.datetime.now()+datetime.timedelta(days=self.days.value())).strftime("%Y-%m-%d")
            self.db.update_user(self.user["id"],self.nome.text(),self.email.text(),new_valid,self.user["is_active"],"")
        else:
            self.db.create_user(self.nome.text(),self.email.text(),self.serial.text(),self.days.value(),"")
        self.accept()


class UsersPage(QWidget):
    def __init__(self, db):
        super().__init__(); self.db=db; self._build()
    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(24,24,24,24); lay.setSpacing(16)
        hdr = QHBoxLayout()
        title = QLabel("Usuários"); title.setStyleSheet(f"font-size:22px;font-weight:700;color:{C['text']};background:transparent;")
        hdr.addWidget(title); hdr.addStretch()
        new_btn = QPushButton("+ Novo"); new_btn.setObjectName("primary")
        new_btn.clicked.connect(self._new); hdr.addWidget(new_btn)
        lay.addLayout(hdr)
        self.table = QTableWidget(0,7)
        self.table.setHorizontalHeaderLabels(["ID","Nome","E-mail","Serial","Válido até","Status","Ações"])
        self.table.horizontalHeader().setSectionResizeMode(1,QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        lay.addWidget(self.table)
        self.refresh()
    def refresh(self):
        users = self.db.get_all_users(); self.table.setRowCount(0)
        for u in users:
            r=self.table.rowCount(); self.table.insertRow(r)
            exp=is_expired(u["valid_until"])
            status = "Expirada" if exp else ("Ativa" if u["is_active"] else "Bloqueada")
            self.table.setItem(r,0,QTableWidgetItem(str(u["id"])))
            self.table.setItem(r,1,QTableWidgetItem(u["nome"]))
            self.table.setItem(r,2,QTableWidgetItem(u["email"] or "—"))
            self.table.setItem(r,3,QTableWidgetItem(u["serial_key"]))
            self.table.setItem(r,4,QTableWidgetItem(format_date_br(u["valid_until"])))
            self.table.setItem(r,5,QTableWidgetItem(status))
            aw=QWidget(); al=QHBoxLayout(aw); al.setContentsMargins(2,2,2,2); al.setSpacing(4)
            for icon,fn in [("Edit",lambda _,uid=u["id"]:self._edit(uid)),
                            ("Bloq",lambda _,uid=u["id"]:self._toggle(uid)),
                            ("Renov",lambda _,uid=u["id"]:self._renew(uid)),
                            ("Lic",lambda _,uid=u["id"]:self._export(uid)),
                            ("Del",lambda _,uid=u["id"]:self._delete(uid))]:
                b=QPushButton(icon); b.setFixedHeight(26); b.clicked.connect(fn); al.addWidget(b)
            self.table.setCellWidget(r,6,aw); self.table.setRowHeight(r,36)
    def _new(self):
        d=UserDialog(self,self.db)
        if d.exec(): self.refresh()
    def _edit(self,uid):
        u=next((x for x in self.db.get_all_users() if x["id"]==uid),None)
        if u:
            d=UserDialog(self,self.db,u)
            if d.exec(): self.refresh()
    def _toggle(self,uid): self.db.toggle_user_active(uid); self.refresh()
    def _renew(self,uid): self.db.renew_user(uid,30); self.refresh()
    def _export(self,uid):
        u=next((x for x in self.db.get_all_users() if x["id"]==uid),None)
        if not u: return
        path,_=QFileDialog.getSaveFileName(self,"Licença",f"{u['nome']}.lic","*.lic")
        if path:
            content=generate_license_file(u["serial_key"],u["nome"],u["valid_until"],u["mac_hash"] or "")
            with open(path,"wb") as f: f.write(content)
            QMessageBox.information(self,"OK",f"Exportado: {path}")
    def _delete(self,uid):
        r=QMessageBox.question(self,"Confirmar","Excluir?",QMessageBox.Yes|QMessageBox.No)
        if r==QMessageBox.Yes: self.db.delete_user(uid); self.refresh()


class EditaisPage(QWidget):
    def __init__(self, db):
        super().__init__(); self.db=db; self._build()
    def _build(self):
        lay=QVBoxLayout(self); lay.setContentsMargins(24,24,24,24); lay.setSpacing(16)
        title=QLabel("Vídeos / Editais")
        title.setStyleSheet(f"font-size:22px;font-weight:700;color:{C['text']};background:transparent;")
        lay.addWidget(title)
        hint=QLabel("Clique duas vezes numa linha para editar os 4 campos de vídeo/link.")
        hint.setStyleSheet(f"color:{C['text3']};font-size:11px;background:transparent;")
        lay.addWidget(hint)
        self.table=QTableWidget(0,4)
        self.table.setHorizontalHeaderLabels(["Categoria","Edital","Edital configurado","Tutorial configurado"])
        self.table.horizontalHeader().setSectionResizeMode(1,QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.cellDoubleClicked.connect(self._dbl)
        lay.addWidget(self.table)
        self._load()
    def _load(self):
        self.table.setRowCount(0)
        config=self.db.get_all_editals_config()
        self._editals=[(p,e) for p,eds in EDITALS_DATA.items() for e in eds]
        for prio,e in self._editals:
            r=self.table.rowCount(); self.table.insertRow(r)
            self.table.setItem(r,0,QTableWidgetItem(prio))
            self.table.setItem(r,1,QTableWidgetItem(e["nome"]))
            edital_ok = bool(config.get(e["id"]+"_edital",e.get("edital_url","")))
            tut_ok = bool(config.get(e["id"]+"_tut","") or config.get(e["id"]+"_acesso",""))
            self.table.setItem(r,2,QTableWidgetItem("Sim" if edital_ok else "Não"))
            self.table.setItem(r,3,QTableWidgetItem("Sim" if tut_ok else "Não"))
            self.table.setRowHeight(r,36)
    def _dbl(self,row,col):
        if row<len(self._editals):
            prio,edital=self._editals[row]
            self._edit_dialog(edital)
    def _edit_dialog(self,edital):
        config=self.db.get_all_editals_config()
        d=QDialog(self); d.setWindowTitle(edital["nome"]); d.setMinimumWidth(560)
        d.setStyleSheet(f"background:{C['surface']};")
        lay=QVBoxLayout(d); lay.setContentsMargins(20,20,20,20); lay.setSpacing(12)
        lay.addWidget(QLabel(edital["nome"],styleSheet=f"font-size:15px;font-weight:700;color:{C['text']};background:transparent;"))
        form=QFormLayout()
        inp_edital=QLineEdit(config.get(edital["id"]+"_edital",edital.get("edital_url","")))
        form.addRow("Link do Edital",inp_edital)
        inp_acesso=QLineEdit(config.get(edital["id"]+"_acesso",""))
        form.addRow("Vídeo Como Acessar",inp_acesso)
        inp_consulta=QLineEdit(config.get(edital["id"]+"_consulta",edital.get("consulta_url","")))
        form.addRow("Link Consulta AIT",inp_consulta)
        inp_tut=QLineEdit(config.get(edital["id"]+"_tut",""))
        form.addRow("Vídeo Como Consultar",inp_tut)
        lay.addLayout(form)
        btns=QHBoxLayout()
        cancel=QPushButton("Cancelar"); cancel.clicked.connect(d.reject)
        save=QPushButton("Salvar"); save.setObjectName("primary")
        def _save():
            from core.tutorials_sync import save_tutorials
            self.db.set_tutorial_url(edital["id"]+"_edital",inp_edital.text().strip())
            self.db.set_tutorial_url(edital["id"]+"_acesso",inp_acesso.text().strip())
            self.db.set_tutorial_url(edital["id"]+"_consulta",inp_consulta.text().strip())
            self.db.set_tutorial_url(edital["id"]+"_tut",inp_tut.text().strip())
            all_config=self.db.get_all_editals_config()
            tut_only={k:v for k,v in all_config.items() if k.endswith("_tut") or k.endswith("_acesso")}
            save_tutorials(tut_only)
            d.accept(); self._load()
            QMessageBox.information(self,"Salvo","Salvo! Faça git push para os clientes receberem.")
        save.clicked.connect(_save)
        btns.addWidget(cancel); btns.addStretch(); btns.addWidget(save)
        lay.addLayout(btns)
        d.exec()


class EditalFormDialog(QDialog):
    def __init__(self,parent,edital=None):
        super().__init__(parent); self.edital=edital
        self.setWindowTitle("Edital"); self.setMinimumWidth(480)
        self.setStyleSheet(f"background:{C['surface']};")
        self._build()
        if edital: self._load()
    def _build(self):
        from core.custom_editals import CATEGORIES
        lay=QVBoxLayout(self); lay.setContentsMargins(20,20,20,20); lay.setSpacing(10)
        form=QFormLayout()
        self.nome=QLineEdit(); form.addRow("Nome",self.nome)
        self.categoria=QComboBox(); self.categoria.addItems(CATEGORIES)
        form.addRow("Categoria",self.categoria)
        self.estado=QLineEdit(); form.addRow("Estado",self.estado)
        self.tipo=QLineEdit(); form.addRow("Tipo",self.tipo)
        self.edital_url=QLineEdit(); form.addRow("Link Edital",self.edital_url)
        self.consulta_url=QLineEdit(); form.addRow("Link Consulta",self.consulta_url)
        self.acesso_url=QLineEdit(); form.addRow("Vídeo Acesso",self.acesso_url)
        self.tut_url=QLineEdit(); form.addRow("Vídeo Consulta",self.tut_url)
        lay.addLayout(form)
        btns=QHBoxLayout()
        cancel=QPushButton("Cancelar"); cancel.clicked.connect(self.reject)
        save=QPushButton("Salvar"); save.setObjectName("primary"); save.clicked.connect(self._save)
        btns.addWidget(cancel); btns.addStretch(); btns.addWidget(save)
        lay.addLayout(btns)
    def _load(self):
        from core.custom_editals import CATEGORIES
        e=self.edital
        self.nome.setText(e.get("nome",""))
        if e.get("_category") in CATEGORIES:
            self.categoria.setCurrentIndex(CATEGORIES.index(e["_category"]))
        self.estado.setText(e.get("estado","")); self.tipo.setText(e.get("tipo",""))
        self.edital_url.setText(e.get("edital_url","")); self.consulta_url.setText(e.get("consulta_url",""))
        self.acesso_url.setText(e.get("acesso_url","")); self.tut_url.setText(e.get("tutorial_url",""))
    def _save(self):
        if not self.nome.text().strip(): return
        from core.custom_editals import make_edital_id
        eid=self.edital.get("id") if self.edital else make_edital_id(self.nome.text())
        self.result_edital={
            "id":eid,"nome":self.nome.text().strip(),"estado":self.estado.text().strip(),
            "tipo":self.tipo.text().strip(),"edital_url":self.edital_url.text().strip(),
            "consulta_url":self.consulta_url.text().strip(),"consulta_url2":"",
            "acesso_url":self.acesso_url.text().strip(),"tutorial_url":self.tut_url.text().strip(),
            "_category":self.categoria.currentText(),
        }
        self.accept()


class GerenciarEditaisPage(QWidget):
    def __init__(self,db):
        super().__init__(); self.db=db; self._build()
    def _build(self):
        lay=QVBoxLayout(self); lay.setContentsMargins(24,24,24,24); lay.setSpacing(16)
        hdr=QHBoxLayout()
        title=QLabel("Gerenciar Editais")
        title.setStyleSheet(f"font-size:22px;font-weight:700;color:{C['text']};background:transparent;")
        hdr.addWidget(title); hdr.addStretch()
        new_btn=QPushButton("+ Novo Edital"); new_btn.setObjectName("primary")
        new_btn.clicked.connect(self._new); hdr.addWidget(new_btn)
        lay.addLayout(hdr)
        self.table=QTableWidget(0,5)
        self.table.setHorizontalHeaderLabels(["Categoria","Nome","Estado","Tipo","Ações"])
        self.table.horizontalHeader().setSectionResizeMode(1,QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        lay.addWidget(self.table)
        self.refresh()
    def refresh(self):
        from core.custom_editals import load_custom_editals
        self.table.setRowCount(0)
        for prio,eds in EDITALS_DATA.items():
            for e in eds: self._row(e,prio,False)
        custom=load_custom_editals()
        for cat,eds in custom.items():
            for e in eds:
                ec=dict(e); ec["_category"]=cat
                self._row(ec,cat,True)
    def _row(self,e,prio,is_custom):
        r=self.table.rowCount(); self.table.insertRow(r)
        self.table.setItem(r,0,QTableWidgetItem(prio))
        self.table.setItem(r,1,QTableWidgetItem(e.get("nome","")))
        self.table.setItem(r,2,QTableWidgetItem(e.get("estado","")))
        self.table.setItem(r,3,QTableWidgetItem(e.get("tipo","")))
        aw=QWidget(); al=QHBoxLayout(aw); al.setContentsMargins(2,2,2,2)
        if is_custom:
            eb=QPushButton("Editar"); eb.clicked.connect(lambda _,ec=dict(e):self._edit(ec))
            db=QPushButton("Excluir"); db.clicked.connect(lambda _,ec=dict(e):self._delete(ec))
            al.addWidget(eb); al.addWidget(db)
        else:
            al.addWidget(QLabel("base",styleSheet=f"color:{C['text3']};background:transparent;"))
        self.table.setCellWidget(r,4,aw); self.table.setRowHeight(r,32)
    def _new(self):
        d=EditalFormDialog(self)
        if d.exec():
            from core.custom_editals import add_edital
            e=d.result_edital; cat=e.pop("_category","Prefeituras")
            add_edital(cat,e); self.refresh()
            QMessageBox.information(self,"OK",f"'{e['nome']}' adicionado!\nFaça git push.")
    def _edit(self,edital):
        d=EditalFormDialog(self,edital)
        if d.exec():
            from core.custom_editals import update_edital,delete_edital,add_edital
            e=d.result_edital; old_cat=edital.get("_category","Prefeituras")
            new_cat=e.pop("_category","Prefeituras")
            if old_cat!=new_cat:
                delete_edital(old_cat,edital["id"]); add_edital(new_cat,e)
            else: update_edital(old_cat,edital["id"],e)
            self.refresh()
    def _delete(self,edital):
        r=QMessageBox.question(self,"Confirmar",f"Excluir {edital.get('nome','')}?",QMessageBox.Yes|QMessageBox.No)
        if r==QMessageBox.Yes:
            from core.custom_editals import delete_edital
            delete_edital(edital.get("_category","Prefeituras"),edital["id"])
            self.refresh()


class SettingsPage(QWidget):
    def __init__(self,db):
        super().__init__(); self.db=db; self._build()
    def _build(self):
        lay=QVBoxLayout(self); lay.setContentsMargins(24,24,24,24); lay.setSpacing(20)
        lay.addWidget(QLabel("Configurações",styleSheet=f"font-size:22px;font-weight:700;color:{C['text']};background:transparent;"))
        r1=QHBoxLayout()
        self.ver=QLineEdit(self.db.get_setting("app_version","1.0.0")); self.ver.setFixedWidth(120)
        r1.addWidget(QLabel("Versão:")); r1.addWidget(self.ver); r1.addStretch()
        lay.addLayout(r1)
        sv=QPushButton("Salvar"); sv.setObjectName("primary")
        sv.clicked.connect(lambda: self.db.set_setting("app_version",self.ver.text()))
        lay.addWidget(sv)
        form=QFormLayout()
        self.old_pw=QLineEdit(); self.old_pw.setEchoMode(QLineEdit.Password)
        self.new_pw=QLineEdit(); self.new_pw.setEchoMode(QLineEdit.Password)
        form.addRow("Senha atual:",self.old_pw); form.addRow("Nova senha:",self.new_pw)
        lay.addLayout(form)
        ch=QPushButton("Alterar Senha"); ch.setObjectName("warning")
        ch.clicked.connect(self._change_pw); lay.addWidget(ch)
        lay.addStretch()
    def _change_pw(self):
        if not self.db.verify_admin(self.old_pw.text()):
            QMessageBox.warning(self,"Erro","Senha incorreta."); return
        if len(self.new_pw.text())<6:
            QMessageBox.warning(self,"Erro","Mínimo 6 caracteres."); return
        self.db.change_admin_password(self.new_pw.text())
        QMessageBox.information(self,"OK","Senha alterada.")


class AdminMain(QWidget):
    def __init__(self,db):
        super().__init__(); self.db=db; self._build()
    def _build(self):
        root=QHBoxLayout(self); root.setContentsMargins(0,0,0,0); root.setSpacing(0)
        side=QWidget(); side.setFixedWidth(200)
        side.setStyleSheet(f"background:{C['sidebar']};border-right:1px solid {C['border']};")
        sl=QVBoxLayout(side); sl.setContentsMargins(10,16,10,16); sl.setSpacing(3)
        logo=QLabel("⚖ Admin"); logo.setStyleSheet(f"color:{C['text']};font-size:14px;font-weight:700;background:transparent;padding:6px;")
        sl.addWidget(logo); sl.addSpacing(10)
        self._pg=QButtonGroup(self); self._pg.setExclusive(True)
        for label,idx in [("Dashboard",0),("Usuários",1),("Vídeos/Editais",2),("Gerenciar Editais",3),("Configurações",4)]:
            btn=QPushButton(label); btn.setObjectName("nav_btn"); btn.setCheckable(True); btn.setFixedHeight(40)
            btn.clicked.connect(lambda _,i=idx: self._switch(i))
            self._pg.addButton(btn); sl.addWidget(btn)
        self._pg.buttons()[0].setChecked(True)
        sl.addStretch()
        root.addWidget(side)
        self.stack=QStackedWidget()
        self.dash=DashboardPage(self.db); self.users=UsersPage(self.db)
        self.editais=EditaisPage(self.db); self.gerenciar=GerenciarEditaisPage(self.db)
        self.settings=SettingsPage(self.db)
        for p in [self.dash,self.users,self.editais,self.gerenciar,self.settings]:
            self.stack.addWidget(p)
        root.addWidget(self.stack)
    def _switch(self,idx):
        self.stack.setCurrentIndex(idx)
        if idx==0: self.dash.refresh()
        elif idx==1: self.users.refresh()
        elif idx==3: self.gerenciar.refresh()


class AdminApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Edital System — Admin"); self.setMinimumSize(1100,700)
        self.db=AdminDB(); self._stk=QStackedWidget(); self.setCentralWidget(self._stk)
        login=LoginScreen(self.db); login.success.connect(self._on_login)
        self._stk.addWidget(login)
        self._main=AdminMain(self.db); self._stk.addWidget(self._main)
    def _on_login(self): self._stk.setCurrentWidget(self._main)


def main():
    app=QApplication(sys.argv); app.setStyle("Fusion")
    pal=QPalette()
    pal.setColor(QPalette.Window,QColor(C["bg"])); pal.setColor(QPalette.WindowText,QColor(C["text"]))
    pal.setColor(QPalette.Base,QColor(C["surface"])); pal.setColor(QPalette.Text,QColor(C["text"]))
    pal.setColor(QPalette.Button,QColor(C["surface"])); pal.setColor(QPalette.ButtonText,QColor(C["text"]))
    app.setPalette(pal); app.setStyleSheet(STYLE)
    win=AdminApp(); win.show(); sys.exit(app.exec())

if __name__=="__main__": main()
