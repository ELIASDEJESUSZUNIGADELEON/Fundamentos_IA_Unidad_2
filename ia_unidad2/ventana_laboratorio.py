"""Interfaz propia: mesa de experimentos con parámetros superiores y población lateral."""

from dataclasses import asdict
from pathlib import Path
import numpy as np
from PySide6.QtCore import QTimer, Qt, QSignalBlocker
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QGroupBox,
    QSplitter,
    QPlainTextEdit,
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
from .optimizacion import Configuracion, MotorGenetico, PROBLEMAS, probabilidades


class Laboratorio(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Unidad 2 · Mesa de evolución")
        self.resize(1260, 850)
        base = QWidget()
        self.setCentralWidget(base)
        raiz = QVBoxLayout(base)
        raiz.setContentsMargins(20, 14, 20, 14)
        cabecera(
            raiz,
            "Mesa de evolución",
            "Optimización binaria y real · Explora la población y compara generaciones.",
        )
        parametros = QGroupBox("Diseño del experimento")
        grid = QGridLayout(parametros)
        self.representacion = opciones(["Binaria", "Real"], "Real")
        self.problema = opciones(PROBLEMAS, "Rastrigin")
        self.dim = entero(2, 1, 8)
        self.pob = entero(80, 4, 400)
        self.generaciones = entero(120, 0, 1000)
        self.semilla = entero(2430085, 0, 2**31 - 1)
        self.precision = decimal(0.001, 1e-9, 1, 9)
        self.seleccion = opciones(["Torneo", "Ruleta", "SUS"])
        self.cruce = opciones(["Monopunto", "Uniforme", "Aritmético", "SBX"], "SBX")
        self.pc = decimal(0.85)
        self.pm = decimal(0.04)
        self.elites = entero(2, 0, 50)
        self.alfa = decimal(0.5)
        self.eta = decimal(5, 0.1, 100, 1)
        campos = [
            ("Representación", self.representacion),
            ("Función", self.problema),
            ("Variables", self.dim),
            ("Población", self.pob),
            ("Generaciones", self.generaciones),
            ("Semilla", self.semilla),
            ("Precisión binaria", self.precision),
            ("Selección", self.seleccion),
            ("Cruce", self.cruce),
            ("P(cruce)", self.pc),
            ("P(mutación)", self.pm),
            ("Élites", self.elites),
            ("Alfa aritmético", self.alfa),
            ("Eta SBX", self.eta),
        ]
        for i, (titulo, w) in enumerate(campos):
            fila, col = divmod(i, 7)
            grid.addWidget(QLabel(titulo), fila * 2, col)
            grid.addWidget(w, fila * 2 + 1, col)
        raiz.addWidget(parametros)
        self.valores = metricas_fila(
            raiz, ["Generación", "Mejor objetivo", "Promedio", "Diversidad"]
        )
        division = QSplitter(Qt.Orientation.Horizontal)
        self.grafica = Grafica(1, 2)
        division.addWidget(self.grafica)
        lateral = QWidget()
        l = QVBoxLayout(lateral)
        l.setContentsMargins(0, 0, 0, 0)
        l.addWidget(QLabel("Población de la generación seleccionada"))
        self.poblacion = tabla(["#", "Genotipo", "Variables", "Objetivo"])
        l.addWidget(self.poblacion, 1)
        self.detalle = QPlainTextEdit()
        self.detalle.setReadOnly(True)
        self.detalle.setMaximumHeight(100)
        l.addWidget(self.detalle)
        division.addWidget(lateral)
        division.setSizes([780, 440])
        raiz.addWidget(division, 1)
        navegacion = QHBoxLayout()
        self.etiqueta = QLabel("G0")
        self.deslizador = QSlider(Qt.Orientation.Horizontal)
        navegacion.addWidget(QLabel("Consultar historial"))
        navegacion.addWidget(self.deslizador, 1)
        navegacion.addWidget(self.etiqueta)
        raiz.addLayout(navegacion)
        controles = QHBoxLayout()
        self.nueva = boton("Nueva corrida", self.reiniciar)
        self.paso_b = boton("Una generación", self.paso)
        self.repro = boton("Reproducir", self.reproducir, True)
        self.pausa = boton("Pausar", self.pausar)
        self.final = boton("Completar", self.completar)
        self.exportar_b = boton("Guardar resultados", self.elegir_exportacion)
        for b in [self.nueva, self.paso_b, self.repro, self.pausa, self.final]:
            controles.addWidget(b)
        controles.addStretch()
        controles.addWidget(self.exportar_b)
        raiz.addLayout(controles)
        self.estado = QLabel()
        self.estado.setWordWrap(True)
        raiz.addWidget(self.estado)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.avanzar)
        self.lote = 1
        self.representacion.currentTextChanged.connect(self.ajustar)
        self.cruce.currentTextChanged.connect(self.ajustar_operadores)
        self.problema.currentTextChanged.connect(self.ajustar_funcion)
        self.deslizador.valueChanged.connect(self.consultar)
        self.ajustar()
        self.reiniciar()

    def ajustar_funcion(self):
        f = PROBLEMAS[self.problema.currentText()]
        self.dim.setEnabled(f.dimensiones_fijas is None)
        if f.dimensiones_fijas:
            self.dim.setValue(f.dimensiones_fijas)

    def ajustar(self):
        binaria = self.representacion.currentText() == "Binaria"
        self.precision.setEnabled(binaria)
        previo = self.cruce.currentText()
        with QSignalBlocker(self.cruce):
            self.cruce.clear()
            self.cruce.addItems(
                ["Monopunto"]
                if binaria
                else ["Monopunto", "Uniforme", "Aritmético", "SBX"]
            )
            self.cruce.setCurrentText(
                "Monopunto" if binaria else previo if previo != "Monopunto" else "SBX"
            )
        self.ajustar_operadores()

    def ajustar_operadores(self):
        self.alfa.setEnabled(self.cruce.currentText() == "Aritmético")
        self.eta.setEnabled(self.cruce.currentText() == "SBX")

    def leer_config(self):
        return Configuracion(
            problema=self.problema.currentText(),
            representacion=self.representacion.currentText(),
            dimensiones=self.dim.value(),
            poblacion=self.pob.value(),
            generaciones=self.generaciones.value(),
            precision=self.precision.value(),
            seleccion=self.seleccion.currentText(),
            cruce=self.cruce.currentText(),
            prob_cruce=self.pc.value(),
            prob_mutacion=self.pm.value(),
            elites=self.elites.value(),
            semilla=self.semilla.value(),
            alfa=self.alfa.value(),
            eta=self.eta.value(),
        )

    def reiniciar(self):
        self.pausar()
        try:
            motor = MotorGenetico(self.leer_config())
        except ValueError as e:
            self.estado.setText(str(e))
            return False
        self.motor = motor
        self.actualizar(0)
        return True

    def pausar(self):
        if hasattr(self, "timer"):
            self.timer.stop()

    def reproducir(self):
        if self.motor.terminado:
            self.estado.setText(
                "Corrida terminada. Crea una nueva para aplicar otros parámetros."
            )
            return
        self.lote = 1
        self.timer.start(100)

    def completar(self):
        self.lote = 8
        self.timer.start(0)

    def paso(self):
        self.pausar()
        self.motor.paso()
        self.actualizar()

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
        for etiqueta, v in zip(
            self.valores,
            [
                str(numero),
                f"{s['mejor']:.6g}",
                f"{s['promedio']:.6g}",
                f"{s['diversidad']:.4f}",
            ],
        ):
            etiqueta.setText(v)
        with QSignalBlocker(self.deslizador):
            self.deslizador.setRange(0, m.numero)
            self.deslizador.setValue(numero)
        self.etiqueta.setText(f"G{numero} / {m.numero}")
        c = m.config
        self.grafica.limpiar()
        ax, bx = self.grafica.ejes
        x = [m.decodificar(g)[0] for g in s["poblacion"]]
        y = s["objetivos"]
        if c.dimensiones == 1:
            a, b = m.problema.dominio
            xx = np.linspace(a, b, 350)
            ax.plot(
                xx, [m.problema.evaluar((v,)) for v in xx], color="#bd8b36", linewidth=1
            )
        ax.scatter(x, y, c="#167462", alpha=0.6, s=20)
        ax.scatter([s["vector"][0]], [s["mejor"]], c="#d27c20", s=70, zorder=4)
        ax.set(
            title="Función y población"
            if c.dimensiones == 1
            else "Proyección x₁ / objetivo completo",
            xlabel="x₁",
            ylabel="Objetivo",
        )
        hist = m.historial[: numero + 1]
        bx.plot(
            [h["generacion"] for h in hist],
            [h["promedio"] for h in hist],
            label="Promedio",
            color="#b18c4d",
        )
        bx.plot(
            [h["generacion"] for h in hist],
            [h["mejor"] for h in hist],
            label="Mejor",
            color="#176b5c",
        )
        bx.plot(
            [h["generacion"] for h in hist],
            [h["historico"] for h in hist],
            label="Histórico",
            linestyle="--",
            color="#51596e",
        )
        bx.set(
            title="Trayectoria de la búsqueda", xlabel="Generación", ylabel="Objetivo"
        )
        bx.legend(fontsize=8)
        self.grafica.draw_idle()
        orden = sorted(
            range(len(y)), key=lambda i: -y[i] if m.problema.maximizar else y[i]
        )
        filas = []
        for i in orden:
            g = s["poblacion"][i]
            gen = (
                "".join(map(str, g)) if c.representacion == "Binaria" else "vector real"
            )
            filas.append(
                [
                    i + 1,
                    gen,
                    ", ".join(f"{v:.5g}" for v in m.decodificar(g)),
                    f"{y[i]:.7g}",
                ]
            )
        llenar_tabla(self.poblacion, filas)
        pesos = probabilidades(y, m.problema.maximizar)
        self.detalle.setPlainText(
            f"{m.problema.formula}\n{'Maximizar' if m.problema.maximizar else 'Minimizar'} · {c.seleccion} · {c.cruce}\nVector mejor: {s['vector']}\nOperaciones de G{numero}: {s['operaciones']}\nPeso ruleta del mejor (referencia): {max(pesos):.3%}"
        )
        self.estado.setText(
            (
                "Límite de generaciones alcanzado. "
                if m.terminado
                else "Corrida preparada. "
            )
            + f"{c.representacion} · semilla {c.semilla} · P(mutación) por {'bit' if c.representacion == 'Binaria' else 'gen'}. Los cambios se aplican en Nueva corrida."
        )

    def elegir_exportacion(self):
        ruta = QFileDialog.getExistingDirectory(self, "Guardar resultados")
        if ruta:
            self.exportar(ruta)

    def exportar(self, ruta):
        ruta = Path(ruta)
        ruta.mkdir(parents=True, exist_ok=True)
        self.actualizar(self.motor.numero)
        guardar_json(
            ruta / "corrida.json",
            {
                "configuracion": asdict(self.motor.config),
                "historial": self.motor.historial,
            },
        )
        guardar_csv(
            ruta / "historial.csv",
            ["generacion", "mejor", "promedio", "historico", "diversidad"],
            [
                [
                    s[k]
                    for k in [
                        "generacion",
                        "mejor",
                        "promedio",
                        "historico",
                        "diversidad",
                    ]
                ]
                for s in self.motor.historial
            ],
        )
        s = self.motor.historial[-1]
        guardar_csv(
            ruta / "poblacion.csv",
            ["id", "genotipo", "variables", "objetivo"],
            [
                [
                    i,
                    "".join(map(str, g))
                    if self.motor.config.representacion == "Binaria"
                    else str(g),
                    str(self.motor.decodificar(g)),
                    s["objetivos"][i],
                ]
                for i, g in enumerate(s["poblacion"])
            ],
        )
        self.grafica.figura.savefig(ruta / "evolucion.png", dpi=150)
        self.estado.setText(f"Resultados guardados en {ruta}")

    def closeEvent(self, event):
        self.pausar()
        super().closeEvent(event)
