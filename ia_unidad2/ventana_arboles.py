"""Explorador propio: árbol y curva juntos; recorridos, datos y evolución debajo."""

from dataclasses import asdict
from pathlib import Path
import math
import random
import numpy as np
from PySide6.QtCore import QTimer, Qt, Signal, QRectF
from PySide6.QtGui import QPainter, QColor, QPen, QFont
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QSplitter,
    QTabWidget,
    QCheckBox,
    QPlainTextEdit,
    QFileDialog,
)
from .interfaz_comun import (
    cabecera,
    boton,
    entero,
    decimal,
    opciones,
    Grafica,
    tabla,
    llenar_tabla,
    guardar_json,
    guardar_csv,
)
from .expresiones import (
    interpretar,
    evaluar,
    curva,
    metricas,
    leer_csv,
    recorridos,
    aleatorio,
    ConfiguracionPG,
    MotorPG,
)


class LienzoArbol(QWidget):
    nodo_elegido = Signal(object)

    def __init__(self):
        super().__init__()
        self.arbol = None
        self.destacado = None
        self.puntos = {}
        self.setMinimumSize(350, 270)

    def establecer(self, arbol):
        self.arbol = arbol
        self.destacado = None
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QColor("white"))
        if self.arbol is None:
            return
        self.puntos = {}
        profundidad = max(1, self.arbol.altura)
        separacion = min(80, (self.height() - 70) / profundidad)

        def ubicar(n, ruta, a, b, nivel):
            x = (a + b) / 2
            y = 33 + nivel * separacion
            self.puntos[ruta] = (x, y, n)
            if len(n.hijos) == 1:
                ubicar(n.hijos[0], ruta + (0,), a, b, nivel + 1)
            elif n.hijos:
                ubicar(n.hijos[0], ruta + (0,), a, x, nivel + 1)
                ubicar(n.hijos[1], ruta + (1,), x, b, nivel + 1)

        ubicar(self.arbol, (), 20, self.width() - 20, 0)
        p.setPen(QPen(QColor("#a8b7aa"), 1.5))
        for ruta, (x, y, n) in self.puntos.items():
            for i, hijo in enumerate(n.hijos):
                xx, yy, _ = self.puntos[ruta + (i,)]
                p.drawLine(int(x), int(y), int(xx), int(yy))
        radio = max(11, min(23, (self.width() - 40) / (2**self.arbol.altura * 2.5)))
        for ruta, (x, y, n) in self.puntos.items():
            p.setBrush(
                QColor(
                    "#d69a36"
                    if ruta == self.destacado
                    else "#216f60"
                    if n.hijos
                    else "#e9efe3"
                )
            )
            p.setPen(
                QPen(QColor("#c48b27" if ruta == self.destacado else "#8faaa0"), 1)
            )
            p.drawEllipse(QRectF(x - radio, y - radio, 2 * radio, 2 * radio))
            p.setPen(
                QColor("white" if n.hijos or ruta == self.destacado else "#234e40")
            )
            p.setFont(QFont("Segoe UI", max(8, min(11, int(radio * 0.5)))))
            texto = n.valor if isinstance(n.valor, str) else f"{n.valor:g}"
            p.drawText(
                QRectF(x - radio, y - radio, 2 * radio, 2 * radio),
                Qt.AlignmentFlag.AlignCenter,
                texto,
            )

    def mousePressEvent(self, event):
        pos = event.position()
        for ruta, (x, y, n) in self.puntos.items():
            if (pos.x() - x) ** 2 + (pos.y() - y) ** 2 < 26**2:
                self.destacado = ruta
                self.update()
                self.nodo_elegido.emit(ruta)
                break


class VentanaArboles(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Unidad 2 · Árboles y curvas")
        self.resize(1240, 830)
        self.datos = None
        self.motor = None
        self.rng_manual = random.Random(2430085)
        central = QWidget()
        self.setCentralWidget(central)
        raiz = QVBoxLayout(central)
        raiz.setContentsMargins(20, 14, 20, 14)
        cabecera(
            raiz,
            "Árboles y curvas",
            "Construye una expresión, recorre sus nodos y descubre fórmulas con programación genética.",
        )
        expresion = QHBoxLayout()
        expresion.addWidget(QLabel("Expresión"))
        self.entrada = QLineEdit("cos(x) + x^3")
        self.entrada.setPlaceholderText("Por ejemplo: (x + 2)*sin(x)")
        expresion.addWidget(self.entrada, 1)
        self.aplicar_b = boton("Construir árbol", self.aplicar, True)
        self.generar_b = boton("Generar al azar", self.generar)
        self.altura_manual = entero(3, 1, 6)
        expresion.addWidget(self.aplicar_b)
        expresion.addWidget(QLabel("Nivel máx."))
        expresion.addWidget(self.altura_manual)
        expresion.addWidget(self.generar_b)
        raiz.addLayout(expresion)
        rangos = QHBoxLayout()
        self.xmin = decimal(-3, -1000, 1000, 3)
        self.xmax = decimal(3, -1000, 1000, 3)
        self.muestras = entero(81, 2, 500)
        self.protegido = QCheckBox("Operaciones protegidas")
        self.protegido.setToolTip(
            "División casi nula → 1; sqrt(|x|); log(max(|x|,1e-12))."
        )
        for nombre, w in [
            ("X desde", self.xmin),
            ("hasta", self.xmax),
            ("Puntos", self.muestras),
        ]:
            rangos.addWidget(QLabel(nombre))
            rangos.addWidget(w)
        rangos.addWidget(self.protegido)
        rangos.addStretch()
        self.csv_b = boton("Cargar CSV x,y", self.elegir_csv)
        self.quitar_b = boton("Quitar datos", self.quitar_datos)
        self.puntos_b = boton("Exportar puntos", self.elegir_puntos)
        rangos.addWidget(self.csv_b)
        rangos.addWidget(self.quitar_b)
        rangos.addWidget(self.puntos_b)
        raiz.addLayout(rangos)
        vista = QSplitter(Qt.Orientation.Horizontal)
        self.lienzo = LienzoArbol()
        self.grafica = Grafica()
        vista.addWidget(self.lienzo)
        vista.addWidget(self.grafica)
        vista.setSizes([600, 640])
        raiz.addWidget(vista, 3)
        self.resumen = QLabel()
        self.resumen.setWordWrap(True)
        raiz.addWidget(self.resumen)
        self.tabs = QTabWidget()
        raiz.addWidget(self.tabs, 2)
        self.crear_recorridos()
        self.crear_datos()
        self.crear_evolucion()
        self.estado = QLabel("Los ángulos usan radianes. La raíz está en el nivel 0.")
        self.estado.setWordWrap(True)
        raiz.addWidget(self.estado)
        self.timer_recorrido = QTimer(self)
        self.timer_recorrido.timeout.connect(self.siguiente_nodo)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.avanzar)
        self.lote = 1
        self.posicion = -1
        self.entrada.returnPressed.connect(self.aplicar)
        self.lienzo.nodo_elegido.connect(self.nodo_seleccionado)
        self.protegido.toggled.connect(lambda _: self.dibujar())
        self.aplicar()

    def crear_recorridos(self):
        panel = QWidget()
        l = QVBoxLayout(panel)
        fila = QHBoxLayout()
        self.modo = opciones(["Preorden", "Inorden", "Postorden"])
        fila.addWidget(QLabel("Orden de visita"))
        fila.addWidget(self.modo)
        self.anterior_b = boton("Anterior", self.anterior_nodo)
        self.siguiente_b = boton("Siguiente nodo", self.siguiente_nodo)
        self.animar_b = boton(
            "Animar recorrido", lambda: self.timer_recorrido.start(550)
        )
        self.detener_b = boton("Pausar recorrido", lambda: self.timer_recorrido.stop())
        for b in [self.anterior_b, self.siguiente_b, self.animar_b, self.detener_b]:
            fila.addWidget(b)
        fila.addStretch()
        l.addLayout(fila)
        self.recorrido_tabla = tabla(["Paso", "Nivel", "Símbolo", "Subexpresión"])
        l.addWidget(self.recorrido_tabla)
        self.modo.currentTextChanged.connect(self.preparar_recorrido)
        self.recorrido_tabla.cellClicked.connect(lambda f, c: self.mostrar_nodo(f))
        self.tabs.addTab(panel, "Recorridos")

    def crear_datos(self):
        panel = QWidget()
        l = QVBoxLayout(panel)
        self.archivo_datos = QLabel(
            "Sin archivo: puedes cargar observaciones CSV con dos columnas x,y."
        )
        l.addWidget(self.archivo_datos)
        self.metricas_label = QLabel()
        l.addWidget(self.metricas_label)
        self.datos_tabla = tabla(["x", "y observada", "y de la expresión", "Error"])
        l.addWidget(self.datos_tabla)
        self.tabs.addTab(panel, "Datos y métricas")

    def crear_evolucion(self):
        panel = QWidget()
        l = QVBoxLayout(panel)
        referencia = QHBoxLayout()
        referencia.addWidget(QLabel("Referencia sin CSV"))
        self.referencia = QLineEdit("x^2 + x + 1")
        referencia.addWidget(self.referencia, 1)
        self.estado_pg = QLabel("Sin corrida")
        referencia.addWidget(self.estado_pg)
        l.addLayout(referencia)
        g = QGridLayout()
        self.pob = entero(100, 8, 300)
        self.generaciones = entero(100, 0, 500)
        self.altura = entero(4, 1, 6)
        self.seleccion = opciones(["Torneo", "Ruleta"])
        self.pc = decimal(0.85)
        self.pm = decimal(0.25)
        self.elites = entero(2, 0, 50)
        self.semilla = entero(2430085, 0, 2**31 - 1)
        self.gramatica = opciones(
            [
                "Básica: + − *",
                "Trigonométrica: + − * sin cos",
                "Ampliada: + − * / sin cos",
            ],
            "Trigonométrica: + − * sin cos",
        )
        for i, (nombre, w) in enumerate(
            [
                ("Población", self.pob),
                ("Generaciones", self.generaciones),
                ("Nivel máx.", self.altura),
                ("Selección", self.seleccion),
                ("P(cruce)", self.pc),
                ("P(mutación)", self.pm),
                ("Élites", self.elites),
                ("Semilla", self.semilla),
            ]
        ):
            g.addWidget(QLabel(nombre), 0, i)
            g.addWidget(w, 1, i)
        l.addLayout(g)
        mutaciones = QHBoxLayout()
        mutaciones.addWidget(QLabel("Mutaciones"))
        self.mutaciones = {}
        for nombre in ["Hojas", "Operadores", "Intercambio", "Subárbol"]:
            c = QCheckBox(nombre)
            c.setChecked(True)
            self.mutaciones[nombre] = c
            mutaciones.addWidget(c)
        mutaciones.addWidget(self.gramatica, 1)
        l.addLayout(mutaciones)
        controles = QHBoxLayout()
        self.nueva_b = boton("Nueva búsqueda", self.iniciar_pg)
        self.paso_pg = boton("Una generación", self.paso)
        self.repro_b = boton("Evolucionar", self.reproducir, True)
        self.pausar_b = boton("Pausar", self.pausar)
        self.completar_b = boton("Completar", self.completar)
        self.usar_b = boton("Ver árbol ganador", self.usar_mejor)
        self.exportar_b = boton("Guardar corrida", self.elegir_exportacion)
        for b in [
            self.nueva_b,
            self.paso_pg,
            self.repro_b,
            self.pausar_b,
            self.completar_b,
            self.usar_b,
            self.exportar_b,
        ]:
            controles.addWidget(b)
        l.addLayout(controles)
        inferior = QSplitter(Qt.Orientation.Horizontal)
        self.poblacion_tabla = tabla(["#", "Expresión", "MSE", "Nodos"])
        self.eventos = QPlainTextEdit()
        self.eventos.setReadOnly(True)
        inferior.addWidget(self.poblacion_tabla)
        inferior.addWidget(self.eventos)
        inferior.setSizes([700, 400])
        l.addWidget(inferior, 1)
        self.tabs.addTab(panel, "Evolución genética")

    def aplicar(self):
        try:
            nuevo = interpretar(self.entrada.text())
            self.validar_intervalo()
        except ValueError as e:
            self.estado.setText(str(e))
            return False
        self.arbol = nuevo
        self.lienzo.establecer(nuevo)
        self.preparar_recorrido()
        self.dibujar()
        return True

    def validar_intervalo(self):
        if self.xmin.value() >= self.xmax.value():
            raise ValueError("El extremo inicial debe ser menor que el final.")

    def generar(self):
        self.arbol = aleatorio(self.rng_manual, self.altura_manual.value())
        self.entrada.setText(self.arbol.texto())
        self.aplicar()

    def preparar_recorrido(self):
        if not hasattr(self, "arbol"):
            return
        self.posicion = -1
        self.visitas = recorridos(self.arbol, self.modo.currentText())
        llenar_tabla(
            self.recorrido_tabla,
            [
                [i + 1, len(r), str(n.valor), n.texto()]
                for i, (r, n) in enumerate(self.visitas)
            ],
        )

    def mostrar_nodo(self, posicion):
        if not self.visitas:
            return
        self.posicion = max(0, min(len(self.visitas) - 1, posicion))
        ruta, n = self.visitas[self.posicion]
        self.lienzo.destacado = ruta
        self.lienzo.update()
        self.recorrido_tabla.selectRow(self.posicion)
        self.estado.setText(
            f"{self.modo.currentText()} · paso {self.posicion + 1}/{len(self.visitas)} · {n.texto()}"
        )

    def siguiente_nodo(self):
        if self.posicion >= len(self.visitas) - 1:
            self.timer_recorrido.stop()
            return
        self.mostrar_nodo(self.posicion + 1)

    def anterior_nodo(self):
        self.timer_recorrido.stop()
        self.mostrar_nodo(self.posicion - 1)

    def nodo_seleccionado(self, ruta):
        self.timer_recorrido.stop()
        indice = next((i for i, (r, n) in enumerate(self.visitas) if r == ruta), 0)
        self.mostrar_nodo(indice)

    def dibujar(self):
        if not hasattr(self, "arbol"):
            return
        try:
            self.validar_intervalo()
        except ValueError as e:
            self.estado.setText(str(e))
            return
        self.grafica.limpiar()
        ax = self.grafica.ejes[0]
        x = np.linspace(self.xmin.value(), self.xmax.value(), 500)
        pred = curva(self.arbol, x, self.protegido.isChecked())
        ax.plot(x, pred, color="#176b5c", linewidth=2, label="Expresión")
        if self.datos is not None:
            xd, yd = self.datos
            ax.scatter(xd, yd, s=20, color="#c79037", label="Observaciones", zorder=4)
            self.actualizar_datos()
        elif self.motor is not None:
            orden = np.argsort(self.motor.x)
            ax.plot(
                self.motor.x[orden],
                self.motor.y[orden],
                "--",
                color="#c79037",
                label="Referencia",
            )
        ax.set(xlabel="x", ylabel="y", title="Curva de la expresión y referencia")
        ax.legend(fontsize=8)
        self.grafica.draw_idle()
        self.resumen.setText(
            f"{self.arbol.tamano} nodos · nivel máximo {self.arbol.altura} · {self.arbol.texto()}"
        )

    def elegir_csv(self):
        ruta, _ = QFileDialog.getOpenFileName(
            self, "Cargar observaciones", "", "CSV (*.csv)"
        )
        if ruta:
            self.cargar_csv(ruta)

    def cargar_csv(self, ruta):
        try:
            datos = leer_csv(ruta)
        except (ValueError, OSError) as e:
            self.estado.setText(str(e))
            return False
        self.pausar()
        self.motor = None
        self.estado_pg.setText("Sin corrida")
        self.datos = datos
        self.archivo_datos.setText(f"{Path(ruta).name} · {len(datos[0])} observaciones")
        a, b = float(min(datos[0])), float(max(datos[0]))
        self.xmin.setValue(a - 1 if a == b else a)
        self.xmax.setValue(b + 1 if a == b else b)
        self.dibujar()
        self.tabs.setCurrentIndex(1)
        return True

    def quitar_datos(self):
        self.pausar()
        self.motor = None
        self.estado_pg.setText("Sin corrida")
        self.datos = None
        self.archivo_datos.setText("Sin archivo CSV.")
        self.metricas_label.setText("")
        self.datos_tabla.setRowCount(0)
        self.dibujar()

    def actualizar_datos(self):
        x, y = self.datos
        p = curva(self.arbol, x, self.protegido.isChecked())
        llenar_tabla(
            self.datos_tabla,
            [
                [
                    f"{a:.6g}",
                    f"{b:.6g}",
                    f"{c:.6g}" if math.isfinite(c) else "Inválido",
                    f"{b - c:.6g}" if math.isfinite(c) else "—",
                ]
                for a, b, c in zip(x[:100], y[:100], p[:100])
            ],
        )
        try:
            m = metricas(y, p)
            self.metricas_label.setText(
                f"MSE {m['mse']:.6g} · RMSE {m['rmse']:.6g} · NMSE {self.numero(m['nmse'])} · R² {self.numero(m['r2'])} · N={m['n']}"
            )
        except ValueError:
            self.metricas_label.setText(
                "Métricas no calculadas: hay predicciones inválidas. Se conservan todas las observaciones."
            )

    @staticmethod
    def numero(valor):
        return "No definido" if valor is None else f"{valor:.6g}"

    def leer_config(self):
        gramatica = self.gramatica.currentIndex()
        operadores = (
            ("+", "-", "*")
            if gramatica == 0
            else ("+", "-", "*", "sin", "cos")
            if gramatica == 1
            else ("+", "-", "*", "/", "sin", "cos")
        )
        return ConfiguracionPG(
            poblacion=self.pob.value(),
            generaciones=self.generaciones.value(),
            altura=self.altura.value(),
            seleccion=self.seleccion.currentText(),
            prob_cruce=self.pc.value(),
            prob_mutacion=self.pm.value(),
            elites=self.elites.value(),
            semilla=self.semilla.value(),
            operadores=operadores,
            mutaciones=tuple(n for n, c in self.mutaciones.items() if c.isChecked()),
            protegido=self.protegido.isChecked(),
        )

    def iniciar_pg(self):
        self.pausar()
        try:
            if self.datos is None:
                self.validar_intervalo()
                x = np.linspace(
                    self.xmin.value(), self.xmax.value(), self.muestras.value()
                )
                y = evaluar(
                    interpretar(self.referencia.text()), x, self.protegido.isChecked()
                )
            else:
                x, y = self.datos
            motor = MotorPG(x, y, self.leer_config())
        except ValueError as e:
            self.estado.setText(str(e))
            return False
        self.motor = motor
        self.actualizar_pg()
        self.dibujar()
        return True

    def pausar(self):
        if hasattr(self, "timer"):
            self.timer.stop()

    def paso(self):
        self.pausar()
        if self.motor is None and not self.iniciar_pg():
            return
        self.motor.paso()
        self.actualizar_pg()

    def reproducir(self):
        if self.motor is None and not self.iniciar_pg():
            return
        self.lote = 1
        if not self.motor.terminado:
            self.timer.start(130)

    def completar(self):
        if self.motor is None and not self.iniciar_pg():
            return
        self.lote = 3
        if not self.motor.terminado:
            self.timer.start(0)

    def avanzar(self):
        for _ in range(self.lote):
            if self.motor.terminado:
                break
            self.motor.paso()
        self.actualizar_pg()
        if self.motor.terminado:
            self.pausar()

    def actualizar_pg(self):
        m = self.motor
        s = m.historial[-1]
        mejor = s["arbol"]
        self.estado_pg.setText(
            f"G{m.numero} · MSE {s['metricas']['mse']:.6g} · válidos {s['validos']}/{m.config.poblacion}"
        )
        llenar_tabla(
            self.poblacion_tabla,
            [
                [
                    i + 1,
                    m.poblacion[i].texto(),
                    f"{m.metricas[i]['mse']:.6g}",
                    m.poblacion[i].tamano,
                ]
                for i in m.orden
            ],
        )
        eventos = s["operaciones"]
        self.eventos.setPlainText(
            "\n\n".join(
                f"{'Cruce' if e['cruce_aplicado'] else 'Copia'} · {e['mutacion']}\n{e['padre']} → {e['hijo']}"
                for e in eventos
            )
            or "G0: inicialización aleatoria; todavía no hay reproducción."
        )
        self.estado.setText(
            (
                "Tolerancia alcanzada. "
                if s["metricas"]["mse"] <= m.config.tolerancia
                else "Límite de generaciones. "
                if m.terminado
                else "Evolución en curso. "
            )
            + f"Mejor: {mejor.texto()} · Pulsa Ver árbol ganador para inspeccionarlo."
        )

    def usar_mejor(self):
        if self.motor is None:
            return
        self.pausar()
        arbol = self.motor.historial[-1]["arbol"]
        self.entrada.setText(arbol.texto())
        # El genotipo se transfiere directamente; no se reconstruye al parsear
        # constantes negativas y se conserva exactamente su cantidad de nodos.
        self.arbol = arbol
        self.lienzo.establecer(arbol)
        self.preparar_recorrido()
        self.dibujar()

    def elegir_exportacion(self):
        if self.motor is None:
            self.estado.setText("Primero ejecuta una búsqueda.")
            return
        ruta = QFileDialog.getExistingDirectory(self, "Guardar programación genética")
        if ruta:
            self.exportar(ruta)

    def exportar(self, ruta):
        if self.motor is None:
            raise ValueError("No hay corrida.")
        self.usar_mejor()
        ruta = Path(ruta)
        ruta.mkdir(parents=True, exist_ok=True)
        m = self.motor
        s = m.historial[-1]
        guardar_json(
            ruta / "regresion.json",
            {
                "configuracion": asdict(m.config),
                "expresion": s["arbol"].texto(),
                "metricas": s["metricas"],
                "historial": m.historial,
            },
        )
        guardar_csv(
            ruta / "historial.csv",
            ["generacion", "mse", "rmse", "r2", "nodos", "validos"],
            [
                [
                    h["generacion"],
                    h["metricas"]["mse"],
                    h["metricas"]["rmse"],
                    h["metricas"]["r2"],
                    h["arbol"].tamano,
                    h["validos"],
                ]
                for h in m.historial
            ],
        )
        p = curva(s["arbol"], m.x, m.config.protegido)
        guardar_csv(
            ruta / "predicciones.csv", ["x", "y", "prediccion"], zip(m.x, m.y, p)
        )
        self.grafica.figura.savefig(ruta / "comparacion.png", dpi=150)
        self.lienzo.grab().save(str(ruta / "arbol.png"))
        self.estado.setText(f"Corrida guardada en {ruta}")

    def elegir_puntos(self):
        try:
            self.validar_intervalo()
        except ValueError as e:
            self.estado.setText(str(e))
            return
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Exportar curva", "puntos.csv", "CSV (*.csv)"
        )
        if ruta:
            x = np.linspace(self.xmin.value(), self.xmax.value(), self.muestras.value())
            y = curva(self.arbol, x, self.protegido.isChecked())
            guardar_csv(
                ruta, ["x", "y"], [(a, b) for a, b in zip(x, y) if math.isfinite(b)]
            )
            self.estado.setText(
                f"Curva exportada: {sum(np.isfinite(y))}/{len(x)} puntos válidos."
            )

    def closeEvent(self, event):
        self.pausar()
        self.timer_recorrido.stop()
        super().closeEvent(event)
