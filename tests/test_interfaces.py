import json
from PySide6.QtCore import Qt
from ia_unidad2.interfaz_comun import preparar_app
from ia_unidad2.ventana_laboratorio import Laboratorio
from ia_unidad2.ventana_reinas import VentanaReinas
from ia_unidad2.ventana_arboles import VentanaArboles


def test_laboratorio_botones_historial_y_exportacion(qtbot, tmp_path):
    preparar_app()
    w = Laboratorio()
    qtbot.addWidget(w)
    w.show()
    w.representacion.setCurrentText("Binaria")
    w.problema.setCurrentText("Máximo oscilatorio")
    w.generaciones.setValue(3)
    qtbot.mouseClick(w.nueva, Qt.MouseButton.LeftButton)
    assert w.motor.config.dimensiones == 1 and w.motor.config.cruce == "Monopunto"
    qtbot.mouseClick(w.paso_b, Qt.MouseButton.LeftButton)
    assert w.motor.numero == 1
    qtbot.mouseClick(w.repro, Qt.MouseButton.LeftButton)
    assert w.timer.isActive()
    qtbot.mouseClick(w.pausa, Qt.MouseButton.LeftButton)
    assert not w.timer.isActive()
    qtbot.mouseClick(w.final, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: w.motor.terminado, timeout=5000)
    w.deslizador.setValue(0)
    assert w.etiqueta.text().startswith("G0")
    w.exportar(tmp_path)
    datos = json.loads((tmp_path / "corrida.json").read_text(encoding="utf-8"))
    assert len(datos["historial"]) == 4 and (tmp_path / "evolucion.png").is_file()


def test_reinas_buscar_inspeccionar_y_exportar(qtbot, tmp_path):
    preparar_app()
    w = VentanaReinas()
    qtbot.addWidget(w)
    w.show()
    w.n.setValue(12)
    w.pob.setValue(100)
    w.generaciones.setValue(500)
    w.reiniciar()
    qtbot.mouseClick(w.resolver, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: w.motor.terminado, timeout=15000)
    assert w.motor.historial[-1]["mejor"] == 0
    w.slider.setValue(0)
    w.seleccionar_individuo(1, 0)
    w.exportar(tmp_path)
    datos = json.loads((tmp_path / "solucion.json").read_text(encoding="utf-8"))
    assert datos["solucion_encontrada"] and datos["ataques"] == []
    assert w.tablero.genes == w.motor.historial[-1]["genes"]


def test_expresiones_datos_recorrido_y_programacion_genetica(qtbot, tmp_path):
    preparar_app()
    w = VentanaArboles()
    qtbot.addWidget(w)
    w.show()
    w.entrada.setText("x^2 + 1")
    qtbot.mouseClick(w.aplicar_b, Qt.MouseButton.LeftButton)
    qtbot.mouseClick(w.siguiente_b, Qt.MouseButton.LeftButton)
    assert w.posicion == 0
    csv = tmp_path / "entrada.csv"
    csv.write_text("x,y\n-1,1\n0,1\n1,3\n2,7\n", encoding="utf-8")
    assert w.cargar_csv(csv)
    w.entrada.setText("x^2 + x + 1")
    w.aplicar()
    assert "MSE 0" in w.metricas_label.text()
    w.tabs.setCurrentIndex(2)
    w.generaciones.setValue(50)
    qtbot.mouseClick(w.nueva_b, Qt.MouseButton.LeftButton)
    qtbot.mouseClick(w.repro_b, Qt.MouseButton.LeftButton)
    qtbot.mouseClick(w.pausar_b, Qt.MouseButton.LeftButton)
    assert not w.timer.isActive()
    qtbot.mouseClick(w.completar_b, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: w.motor.terminado, timeout=30000)
    assert w.motor.historial[-1]["metricas"]["mse"] < 1e-5
    w.exportar(tmp_path / "salida")
    datos = json.loads((tmp_path / "salida/regresion.json").read_text(encoding="utf-8"))
    assert datos["metricas"]["n"] == 4
    assert (tmp_path / "salida/arbol.png").is_file()
    w.quitar_datos()
    assert w.motor is None


def test_error_de_expresion_conserva_arbol_valido(qtbot):
    preparar_app()
    w = VentanaArboles()
    qtbot.addWidget(w)
    previo = w.arbol
    w.entrada.setText("x+(")
    assert not w.aplicar() and w.arbol is previo
