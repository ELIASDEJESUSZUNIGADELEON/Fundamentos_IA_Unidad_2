"""Comprueba los cuatro recorridos y captura la ventana real del equipo."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
PROYECTO = ROOT / "02-visualizador-de-grafos"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--visible", action="store_true")
    args = parser.parse_args()
    if not args.visible:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(PROYECTO))
    from PySide6.QtGui import QFont
    from PySide6.QtWidgets import QApplication
    from ia_unidad2.interfaz_comun import cargar_fuentes
    from aplicacion import ALGORITMOS, Laboratorio

    app = QApplication.instance() or QApplication([])
    cargar_fuentes()
    app.setFont(QFont("Segoe UI", 10))
    ventana = Laboratorio()
    ventana.resize(1720, 1050)
    ventana.show()
    resultados = {}
    for algoritmo in ALGORITMOS:
        ventana.mostrar(algoritmo.clave)
        assert ventana.actual == algoritmo.clave
        vista = ventana.vistas[algoritmo.clave]
        recorrido = vista.recorrido
        final = recorrido.pasos[-1]
        if algoritmo.clave == "floyd-warshall":
            vista.ir_a(len(recorrido.pasos) - 1)
            ruta, aristas = recorrido.ruta(final, 13, 69)
            costo = final.distancias[recorrido.nodos.index(13)][
                recorrido.nodos.index(69)
            ]
        else:
            vista.resultado()
            ruta, aristas, costo = (
                recorrido.ruta,
                recorrido.aristas_ruta,
                recorrido.costo,
            )
        assert list(ruta) == [13, 16, 17, 69] and costo == 14
        pesos = {arista.id: arista.peso for arista in vista.grafo.aristas}
        assert sum(pesos[identificador] for identificador in aristas) == costo
        resultados[algoritmo.clave] = {
            "ruta": list(ruta),
            "aristas": list(aristas),
            "costo": costo,
            "pasos": len(recorrido.pasos),
            "nodos": len(vista.grafo.posiciones),
        }
        app.processEvents()
        print(
            f"{algoritmo.nombre}: {' -> '.join(map(str, ruta))}, costo {costo}",
            flush=True,
        )

    ventana.mostrar("dijkstra")
    app.processEvents()
    captura = ROOT / "capturas/02-grafos.png"
    captura.parent.mkdir(exist_ok=True)
    assert ventana.grab().save(str(captura))
    destino = PROYECTO / "resultados/verificacion_equipo.json"
    destino.parent.mkdir(exist_ok=True)
    destino.write_text(
        json.dumps(
            {
                "fecha_utc": datetime.now(timezone.utc).isoformat(),
                "equipo": [
                    "Elias de Jesus Zuñiga de Leon",
                    "OSVALDO FABIAN RAMIRO BALBOA",
                ],
                "resultados": resultados,
                "captura": "capturas/02-grafos.png",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    ventana.close()
    print("Captura: 02-grafos.png", flush=True)


if __name__ == "__main__":
    main()
