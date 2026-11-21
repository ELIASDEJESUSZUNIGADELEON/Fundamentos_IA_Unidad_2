"""Componentes visuales y exportación compartidos por las interfaces propias."""

import csv
import json
import math
from pathlib import Path
from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QSpinBox,
    QDoubleSpinBox,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

RAIZ = Path(__file__).resolve().parents[1]
ESTILO = """
QWidget { font-family: 'Segoe UI'; font-size: 12px; color: #263b3b; }
QMainWindow { background: #f5f4ee; }
QLabel#Titulo { font-size: 25px; font-weight: 650; color: #154e48; }
QLabel#Subtitulo { color: #65736c; }
QLabel#Valor { font-size: 21px; font-weight: 650; color: #155c52; }
QFrame#Tarjeta, QGroupBox { background: #ffffff; border: 1px solid #dedfd7; border-radius: 6px; }
QGroupBox { margin-top: 9px; padding-top: 13px; font-weight: 600; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 5px; }
QPushButton { background: #ffffff; border: 1px solid #c9d0c8; padding: 8px 14px; border-radius: 5px; }
QPushButton:hover { background: #e7efea; border-color: #579380; }
QPushButton:pressed { background: #cfe1d8; }
QPushButton#Principal { background: #176b5c; color: white; border-color: #176b5c; font-weight: 600; }
QPushButton#Principal:hover { background: #125748; }
QPushButton:disabled { background: #eeeee8; color: #a2aaa4; border-color: #ddd; }
QLineEdit,QSpinBox,QDoubleSpinBox,QComboBox { background: white; color: #263b3b; border: 1px solid #cbd3cc; border-radius: 4px; padding: 5px; min-height: 18px; }
QTableWidget { background: white; alternate-background-color: #f5f7f3; gridline-color: #e5e8df; border: 1px solid #dce1d8; }
QHeaderView::section { background: #eaf0e9; border: none; border-bottom: 1px solid #d3ded1; padding: 6px; font-weight: 600; }
QTabWidget::pane { border: 1px solid #dedfd7; background: white; }
QTabBar::tab { background: #e8ebe3; padding: 8px 17px; border: 1px solid #d7ded4; }
QTabBar::tab:selected { background: white; color: #126252; font-weight: 600; }
QTextEdit,QPlainTextEdit,QListWidget { background: white; border: 1px solid #d4dcd1; padding: 6px; }
QSlider::groove:horizontal { height: 5px; background: #d9e1d5; }
QSlider::handle:horizontal { background: #176b5c; width: 14px; margin: -5px 0; border-radius: 7px; }
"""


def cargar_fuentes():
    """Qt offscreen no siempre registra las fuentes de Windows automáticamente."""
    for nombre in ["segoeui.ttf", "seguisb.ttf", "seguisym.ttf"]:
        ruta = Path("C:/Windows/Fonts") / nombre
        if ruta.exists():
            QFontDatabase.addApplicationFont(str(ruta))


def preparar_app():
    app = QApplication.instance() or QApplication([])
    cargar_fuentes()
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))
    app.setStyleSheet(ESTILO)
    return app


def cabecera(layout, titulo, subtitulo):
    t = QLabel(titulo)
    t.setObjectName("Titulo")
    layout.addWidget(t)
    s = QLabel(subtitulo)
    s.setObjectName("Subtitulo")
    s.setWordWrap(True)
    layout.addWidget(s)


def boton(texto, accion, principal=False):
    b = QPushButton(texto)
    b.clicked.connect(accion)
    if principal:
        b.setObjectName("Principal")
    return b


def entero(valor, minimo, maximo):
    w = QSpinBox()
    w.setRange(minimo, maximo)
    w.setValue(valor)
    return w


def decimal(valor, minimo=0, maximo=1, decimales=3):
    w = QDoubleSpinBox()
    w.setDecimals(decimales)
    w.setRange(minimo, maximo)
    w.setSingleStep(0.01)
    w.setValue(valor)
    return w


def opciones(items, actual=None):
    w = QComboBox()
    w.addItems(list(items))
    if actual is not None:
        w.setCurrentText(actual)
    return w


def tarjeta(titulo):
    frame = QFrame()
    frame.setObjectName("Tarjeta")
    l = QVBoxLayout(frame)
    l.setContentsMargins(13, 8, 13, 8)
    subt = QLabel(titulo)
    subt.setObjectName("Subtitulo")
    valor = QLabel("—")
    valor.setObjectName("Valor")
    l.addWidget(subt)
    l.addWidget(valor)
    return frame, valor


def metricas_fila(layout, titulos):
    fila = QHBoxLayout()
    valores = []
    for titulo in titulos:
        frame, valor = tarjeta(titulo)
        fila.addWidget(frame, 1)
        valores.append(valor)
    layout.addLayout(fila)
    return valores


class Grafica(FigureCanvasQTAgg):
    def __init__(self, filas=1, columnas=1):
        self.figura = Figure(figsize=(7, 3), facecolor="white", layout="constrained")
        super().__init__(self.figura)
        self.ejes = self.figura.subplots(filas, columnas, squeeze=False).flat
        self.ejes = list(self.ejes)
        self.setMinimumHeight(190)

    def limpiar(self):
        for ax in self.ejes:
            ax.clear()
            ax.spines[["top", "right"]].set_visible(False)
            ax.grid(alpha=0.16)


def tabla(encabezados):
    w = QTableWidget(0, len(encabezados))
    w.setHorizontalHeaderLabels(encabezados)
    w.setAlternatingRowColors(True)
    w.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    w.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    w.verticalHeader().setVisible(False)
    w.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
    w.horizontalHeader().setStretchLastSection(True)
    return w


def llenar_tabla(w, filas):
    w.setRowCount(len(filas))
    for i, fila in enumerate(filas):
        for j, valor in enumerate(fila):
            item = QTableWidgetItem(str(valor))
            item.setToolTip(str(valor))
            w.setItem(i, j, item)


def limpio(valor):
    if isinstance(valor, float) and not math.isfinite(valor):
        return None
    if isinstance(valor, dict):
        return {str(k): limpio(v) for k, v in valor.items()}
    if isinstance(valor, (tuple, list)):
        return [limpio(v) for v in valor]
    if hasattr(valor, "texto"):
        return valor.texto()
    return valor


def guardar_json(ruta, datos):
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(
        json.dumps(limpio(datos), ensure_ascii=False, indent=2, allow_nan=False),
        encoding="utf-8",
    )


def guardar_csv(ruta, campos, filas):
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(campos)
        w.writerows(filas)
