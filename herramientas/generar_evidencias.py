"""Ejecuta las aplicaciones reales, exporta resultados y captura sus widgets Qt."""

import argparse
from dataclasses import asdict
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "01-problema-hormiga/src"))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--visible", action="store_true")
    args = p.parse_args()
    if not args.visible:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    from ia_unidad2.interfaz_comun import (
        preparar_app,
        guardar_json,
        guardar_csv,
        Grafica,
        cargar_fuentes,
    )
    from ant_pathfinding.presentation.qt.main_window import MainWindow
    from ant_pathfinding.search.algorithms import SearchAlgorithm, solve

    app = QApplication.instance() or QApplication([])
    cargar_fuentes()
    from PySide6.QtGui import QFont

    app.setFont(QFont("Segoe UI", 10))
    capturas = ROOT / "capturas"
    capturas.mkdir(exist_ok=True)
    resumen = {}

    def captura(w, nombre):
        w.show()
        app.processEvents()
        for c in w.findChildren(Grafica):
            c.draw()
        app.processEvents()
        destino = capturas / nombre
        if not w.grab().save(str(destino)):
            raise RuntimeError("No se pudo guardar " + str(destino))
        print("Captura:", nombre, flush=True)

    # La aplicación del equipo se conserva sin modificar.
    hormiga = MainWindow()
    hormiga.resize(1160, 760)
    hormiga.foods_spin.setValue(3)
    hormiga.seed_spin.setValue(2430085)
    hormiga.ratio_spin.setValue(0.18)
    hormiga.generate()
    hormiga.show()
    app.processEvents()
    escenario = hormiga.editor.scenario
    resultados = {}
    for algoritmo in SearchAlgorithm:
        r = solve(algoritmo, escenario)
        assert r.found and set(escenario.foods) <= set(r.path)
        assert r.path[0] == escenario.start and r.path[-1] == escenario.goal
        assert all(
            abs(a.x - b.x) + abs(a.y - b.y) == 1 for a, b in zip(r.path, r.path[1:])
        )
        resultados[algoritmo.value] = {
            "encontrada": r.found,
            "costo": r.cost,
            "expandidos": r.expanded_states,
            "ruta": [[p.x, p.y] for p in r.path],
        }
    assert len({r["costo"] for r in resultados.values()}) == 1
    panel = hormiga.search_panel
    panel.algorithm_combo.setCurrentIndex(2)
    panel.burst_combo.setCurrentIndex(2)
    panel.run_button.click()
    inicio = time.monotonic()
    while panel._runner is None or not panel._runner.finished:
        app.processEvents()
        if time.monotonic() - inicio > 45:
            raise RuntimeError("La búsqueda gráfica de la hormiga no terminó.")
    for _ in range(len(panel._path)):
        panel.playback_step_button.click()
    app.processEvents()
    captura(hormiga, "01-hormiga.png")
    guardar_json(
        ROOT / "01-problema-hormiga/resultados/verificacion_equipo.json",
        {
            "semilla": 2430085,
            "alimentos": len(escenario.foods),
            "obstaculos": len(escenario.grid.blocked),
            "resultados": resultados,
        },
    )
    resumen["hormiga"] = {
        "alimentos": len(escenario.foods),
        "costo": resultados["astar"]["costo"],
        "tres_algoritmos_coinciden": True,
    }
    hormiga.close()

    preparar_app()
    from ia_unidad2.ventana_laboratorio import Laboratorio
    from ia_unidad2.ventana_reinas import VentanaReinas
    from ia_unidad2.ventana_arboles import VentanaArboles
    import numpy as np

    laboratorio = Laboratorio()
    laboratorio.representacion.setCurrentText("Binaria")
    laboratorio.problema.setCurrentText("Máximo oscilatorio")
    laboratorio.generaciones.setValue(100)
    assert laboratorio.reiniciar()
    laboratorio.motor.ejecutar()
    laboratorio.actualizar()
    laboratorio.exportar(ROOT / "03-lab-algoritmos-evolutivos/resultados/binario")
    captura(laboratorio, "03-1-binario.png")
    resumen["binario"] = {
        "configuracion": asdict(laboratorio.motor.config),
        "mejor": laboratorio.motor.historial[-1]["mejor"],
        "vector": laboratorio.motor.historial[-1]["vector"],
    }

    laboratorio.representacion.setCurrentText("Real")
    laboratorio.problema.setCurrentText("Rastrigin")
    laboratorio.dim.setValue(3)
    laboratorio.cruce.setCurrentText("SBX")
    laboratorio.generaciones.setValue(150)
    assert laboratorio.reiniciar()
    laboratorio.motor.ejecutar()
    laboratorio.actualizar()
    laboratorio.exportar(ROOT / "03-lab-algoritmos-evolutivos/resultados/real")
    captura(laboratorio, "03-2-real.png")
    resumen["real"] = {
        "configuracion": asdict(laboratorio.motor.config),
        "mejor": laboratorio.motor.historial[-1]["mejor"],
        "vector": laboratorio.motor.historial[-1]["vector"],
    }
    laboratorio.close()

    reinas = VentanaReinas()
    reinas.motor.ejecutar()
    reinas.actualizar()
    assert reinas.motor.historial[-1]["mejor"] == 0
    reinas.exportar(ROOT / "04-n-reinas/resultados")
    captura(reinas, "04-reinas.png")
    resumen["reinas"] = {
        "n": reinas.motor.config.n,
        "generacion": reinas.motor.numero,
        "conflictos": 0,
        "filas": [g + 1 for g in reinas.motor.historial[-1]["genes"]],
    }
    reinas.close()

    arboles = VentanaArboles()
    arboles.entrada.setText("sin(x) * (x + 1)")
    assert arboles.aplicar()
    arboles.modo.setCurrentText("Postorden")
    arboles.mostrar_nodo(4)
    captura(arboles, "05-1-expresion.png")
    x = np.linspace(-3, 3, 81)
    y = x * x + x + 1
    datos = ROOT / "05-arboles-expresion/datos/ejemplo_cuadratico.csv"
    guardar_csv(datos, ["x", "y"], zip(x, y))
    assert arboles.cargar_csv(datos)
    arboles.tabs.setCurrentIndex(2)
    assert arboles.iniciar_pg()
    arboles.motor.ejecutar()
    arboles.actualizar_pg()
    arboles.usar_mejor()
    arboles.exportar(ROOT / "05-arboles-expresion/resultados")
    captura(arboles, "05-2-programacion-genetica.png")
    resultado = arboles.motor.historial[-1]
    resumen["arboles"] = {
        "generacion": arboles.motor.numero,
        "expresion": resultado["arbol"].texto(),
        "metricas": resultado["metricas"],
        "muestras": len(x),
    }
    arboles.close()
    guardar_json(ROOT / "capturas/resultados_demostraciones.json", resumen)
    print(json.dumps(resumen, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
