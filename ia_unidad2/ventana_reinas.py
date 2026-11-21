"""Tablero grande, controles a la derecha e inspección de individuos."""

from dataclasses import asdict
from pathlib import Path
from PySide6.QtCore import QTimer, Qt, QSignalBlocker, QRectF
from PySide6.QtGui import QPainter, QColor, QPen, QFont
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QGroupBox,
    QLabel,
    QSlider,
    QFileDialog,
)
from .interfaz_comun import (
    cabecera,
    boton,
    entero,
    decimal,
    opciones,
    metricas_fila,
    Grafica,
    tabla,
    llenar_tabla,
    guardar_json,
    guardar_csv,
)
from .reinas import ConfiguracionReinas, MotorReinas, ataques


class Tablero(QWidget):
    def __init__(self):
        super().__init__()
        self.genes = ()
        self.setMinimumSize(380, 380)

    def establecer(self, genes):
        self.genes = tuple(genes)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QColor("#ffffff"))
        if not self.genes:
            return
        n = len(self.genes)
        lado = min(self.width() - 66, self.height() - 66)
        celda = lado / n
        ox = (self.width() - lado) / 2
        oy = (self.height() - lado) / 2
        for r in range(n):
            for c in range(n):
                p.fillRect(
                    QRectF(ox + c * celda, oy + r * celda, celda, celda),
                    QColor("#e7e8db" if (r + c) % 2 == 0 else "#91b0a3"),
                )
        parejas = ataques(self.genes)
        amenazadas = {i for par in parejas for i in par}
        p.setPen(QPen(QColor("#bc5a54"), 1.5))
        for a, b in parejas:
            p.drawLine(
                int(ox + (a + 0.5) * celda),
                int(oy + (self.genes[a] + 0.5) * celda),
                int(ox + (b + 0.5) * celda),
                int(oy + (self.genes[b] + 0.5) * celda),
            )
        for c, r in enumerate(self.genes):
            p.setFont(QFont("Segoe UI Symbol", max(9, int(celda * 0.49))))
            p.setPen(QColor("#9d302c" if c in amenazadas else "#123f38"))
            p.drawText(
                QRectF(ox + c * celda, oy + r * celda, celda, celda),
                Qt.AlignmentFlag.AlignCenter,
                "♛",
            )
        p.setFont(QFont("Segoe UI", 9))
        p.setPen(QColor("#58645b"))
        for i in range(n):
            p.drawText(
                QRectF(ox + i * celda, oy + lado + 4, celda, 22),
                Qt.AlignmentFlag.AlignCenter,
                str(i + 1),
            )
            p.drawText(
                QRectF(ox - 28, oy + i * celda, 24, celda),
                Qt.AlignmentFlag.AlignCenter,
                str(i + 1),
            )


class VentanaReinas(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Unidad 2 · Reinas en equilibrio")
        self.resize(1200, 800)
        central = QWidget()
        self.setCentralWidget(central)
        raiz = QVBoxLayout(central)
        raiz.setContentsMargins(20, 14, 20, 14)
        cabecera(
            raiz,
            "Reinas en equilibrio",
            "Una reina por fila y columna. El reto es eliminar los ataques diagonales.",
        )
        self.valores = metricas_fila(
            raiz, ["Generación", "Pares en conflicto", "Promedio", "Tableros distintos"]
        )
        cuerpo = QHBoxLayout()
        izquierda = QVBoxLayout()
        self.tablero = Tablero()
        izquierda.addWidget(self.tablero, 1)
        self.vector = QLabel()
        self.vector.setAlignment(Qt.AlignmentFlag.AlignCenter)
        izquierda.addWidget(self.vector)
        self.curva = Grafica()
        self.curva.setMaximumHeight(225)
        izquierda.addWidget(self.curva)
        cuerpo.addLayout(izquierda, 3)
        derecha = QVBoxLayout()
        panel = QGroupBox("Preparar la búsqueda")
        form = QFormLayout(panel)
        self.n = entero(12, 1, 32)
        self.pob = entero(100, 4, 300)
        self.generaciones = entero(500, 0, 1000)
        self.pc = decimal(0.9)
        self.pm = decimal(0.22)
        self.elites = entero(2, 0, 50)
        self.seleccion = opciones(["Torneo", "Ruleta"])
        self.cruce = opciones(["Orden OX", "Ciclos CX"])
        self.semilla = entero(2430085, 0, 2**31 - 1)
        for titulo, w in [
            ("Reinas / lado", self.n),
            ("Población", self.pob),
            ("Generaciones", self.generaciones),
            ("Selección", self.seleccion),
            ("Cruce", self.cruce),
            ("P(cruce)", self.pc),
            ("P(intercambio)", self.pm),
            ("Élites", self.elites),
            ("Semilla", self.semilla),
        ]:
            form.addRow(titulo, w)
        derecha.addWidget(panel)
        self.nueva = boton("Preparar tablero", self.reiniciar)
        self.resolver = boton("Buscar solución", self.completar, True)
        self.paso_b = boton("Una generación", self.paso)
        self.repro = boton("Reproducir", self.reproducir)
        self.pausa = boton("Pausar", self.pausar)
        derecha.addWidget(self.nueva)
        derecha.addWidget(self.resolver)
        botones = QHBoxLayout()
        for b in [self.paso_b, self.repro, self.pausa]:
            botones.addWidget(b)
        derecha.addLayout(botones)
        derecha.addWidget(QLabel("Selecciona un individuo para ver su tablero"))
        self.tabla = tabla(["ID", "Filas por columna", "Conflictos"])
        derecha.addWidget(self.tabla, 1)
        self.exportar_b = boton("Guardar corrida", self.elegir_exportacion)
        derecha.addWidget(self.exportar_b)
        cuerpo.addLayout(derecha, 2)
        raiz.addLayout(cuerpo, 1)
        navegacion = QHBoxLayout()
        navegacion.addWidget(QLabel("Historial"))
        self.slider = QSlider(Qt.Orientation.Horizontal)
        navegacion.addWidget(self.slider, 1)
        self.pagina = QLabel()
        navegacion.addWidget(self.pagina)
        raiz.addLayout(navegacion)
        self.estado = QLabel()
        self.estado.setWordWrap(True)
        raiz.addWidget(self.estado)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.avanzar)
        self.lote = 1
        self.slider.valueChanged.connect(self.consultar)
        self.tabla.cellClicked.connect(self.seleccionar_individuo)
        self.reiniciar()

    def leer_config(self):
        return ConfiguracionReinas(
            n=self.n.value(),
            poblacion=self.pob.value(),
            generaciones=self.generaciones.value(),
            prob_cruce=self.pc.value(),
            prob_mutacion=self.pm.value(),
            elites=self.elites.value(),
            seleccion=self.seleccion.currentText(),
            cruce=self.cruce.currentText(),
            semilla=self.semilla.value(),
        )

    def reiniciar(self):
        self.pausar()
        try:
            motor = MotorReinas(self.leer_config())
        except ValueError as e:
            self.estado.setText(str(e))
            return False
        self.motor = motor
        self.actualizar(0)
        return True

    def pausar(self):
        if hasattr(self, "timer"):
            self.timer.stop()

    def paso(self):
        self.pausar()
        self.motor.paso()
        self.actualizar()

    def reproducir(self):
        if not self.motor.terminado:
            self.lote = 1
            self.timer.start(120)

    def completar(self):
        if not self.motor.terminado:
            self.lote = 25
            self.timer.start(0)

    def avanzar(self):
        for _ in range(self.lote):
            if self.motor.terminado:
                break
            self.motor.paso()
        self.actualizar()
        if self.motor.terminado:
            self.pausar()

    def consultar(self, numero):
        self.pausar()
        self.actualizar(numero)

    def actualizar(self, numero=None):
        m = self.motor
        numero = m.numero if numero is None else numero
        s = m.historial[numero]
        self.vista = numero
        for w, v in zip(
            self.valores, [numero, s["mejor"], f"{s['promedio']:.2f}", s["distintos"]]
        ):
            w.setText(str(v))
        with QSignalBlocker(self.slider):
            self.slider.setRange(0, m.numero)
            self.slider.setValue(numero)
        self.pagina.setText(f"G{numero} / {m.numero}")
        self.tablero.establecer(s["genes"])
        self.vector.setText(
            "Filas por columna: " + ", ".join(str(v + 1) for v in s["genes"])
        )
        self.orden_vista = sorted(
            range(len(s["poblacion"])), key=lambda i: s["conflictos"][i]
        )
        llenar_tabla(
            self.tabla,
            [
                [
                    i + 1,
                    ", ".join(str(g + 1) for g in s["poblacion"][i]),
                    s["conflictos"][i],
                ]
                for i in self.orden_vista
            ],
        )
        self.curva.limpiar()
        ax = self.curva.ejes[0]
        hist = m.historial[: numero + 1]
        ax.plot(
            [h["generacion"] for h in hist],
            [h["promedio"] for h in hist],
            color="#c59b50",
            label="Promedio",
        )
        ax.plot(
            [h["generacion"] for h in hist],
            [h["mejor"] for h in hist],
            color="#176b5c",
            label="Mejor",
        )
        ax.set(xlabel="Generación", ylabel="Pares en conflicto")
        ax.legend(fontsize=8)
        self.curva.draw_idle()
        if s["mejor"] == 0:
            mensaje = "Solución comprobada: ninguna pareja comparte diagonal."
        elif m.terminado:
            mensaje = (
                "Límite alcanzado sin solución. Prueba otra semilla o más generaciones."
            )
        else:
            mensaje = "Reinas rojas: participan en ataques. Las líneas indican las parejas en conflicto."
        self.estado.setText(
            mensaje + f"  G{numero} · {s['operaciones']} · semilla {m.config.semilla}"
        )

    def seleccionar_individuo(self, fila, columna):
        self.pausar()
        s = self.motor.historial[self.vista]
        idx = self.orden_vista[fila]
        genes = s["poblacion"][idx]
        self.tablero.establecer(genes)
        self.vector.setText(
            f"Individuo {idx + 1} · Filas: {', '.join(str(v + 1) for v in genes)} · {s['conflictos'][idx]} conflictos"
        )

    def elegir_exportacion(self):
        ruta = QFileDialog.getExistingDirectory(self, "Guardar búsqueda")
        if ruta:
            self.exportar(ruta)

    def exportar(self, ruta):
        ruta = Path(ruta)
        ruta.mkdir(parents=True, exist_ok=True)
        self.actualizar(self.motor.numero)
        s = self.motor.historial[-1]
        guardar_json(
            ruta / "solucion.json",
            {
                "configuracion": asdict(self.motor.config),
                "solucion_encontrada": s["mejor"] == 0,
                "generacion": s["generacion"],
                "filas_base_uno": [g + 1 for g in s["genes"]],
                "ataques": ataques(s["genes"]),
                "historial": self.motor.historial,
            },
        )
        guardar_csv(
            ruta / "historial.csv",
            ["generacion", "mejor", "promedio", "distintos"],
            [
                [h[k] for k in ["generacion", "mejor", "promedio", "distintos"]]
                for h in self.motor.historial
            ],
        )
        self.tablero.grab().save(str(ruta / "tablero.png"))
        self.curva.figura.savefig(ruta / "convergencia.png", dpi=150)
        self.estado.setText(f"Resultados guardados en {ruta}")

    def closeEvent(self, event):
        self.pausar()
        super().closeEvent(event)
