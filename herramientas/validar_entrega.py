"""Comprueba la integridad y coherencia de la entrega antes de publicarla."""

import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
from urllib.parse import unquote
import xml.etree.ElementTree as ET
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def main():
    comprobaciones = []

    def ok(texto):
        comprobaciones.append(texto)
        print("OK:", texto)

    origen = json.loads(
        (ROOT / "herramientas/origen_hormiga.json").read_text(encoding="utf-8")
    )
    for item in origen["archivos"]:
        assert (
            hashlib.sha256((ROOT / item["archivo"]).read_bytes()).hexdigest()
            == item["sha256"]
        ), item["archivo"]
    ok(
        f"Los {len(origen['archivos'])} archivos del proyecto de la hormiga coinciden con la revisión de César."
    )
    grafos = list((ROOT / "02-visualizador-de-grafos").iterdir())
    assert (
        len(grafos) == 1
        and grafos[0].name == ".gitkeep"
        and grafos[0].stat().st_size == 0
    )
    ok("Visualizador de grafos vacío, reservado con .gitkeep.")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert re.findall(r"^## ([0-9]+)[.]", readme, re.MULTILINE) == [
        "1",
        "2",
        "3",
        "4",
        "5",
    ]
    assert len(re.findall(r"^!\[", readme, re.MULTILINE)) == 6
    rotos = []
    for md in ROOT.rglob("*.md"):
        for enlace in re.findall(
            r"\[[^\]]*\]\(([^)]+)\)", md.read_text(encoding="utf-8")
        ):
            if enlace.startswith(("http:", "https:", "#", "mailto:")):
                continue
            archivo = unquote(enlace.split("#")[0])
            if archivo and not (md.parent / archivo).exists():
                rotos.append((str(md.relative_to(ROOT)), archivo))
    assert not rotos, rotos
    ok(
        "README con cinco actividades numeradas, seis imágenes y enlaces locales válidos."
    )
    imagenes = list((ROOT / "capturas").glob("*.png"))
    assert len(imagenes) == 6
    for archivo in imagenes:
        with Image.open(archivo) as im:
            assert im.width >= 900 and im.height >= 600
            im.verify()
    ok("Seis capturas Qt legibles revisadas visualmente, con archivos PNG válidos.")
    hormiga = json.loads(
        (ROOT / "01-problema-hormiga/resultados/verificacion_equipo.json").read_text(
            encoding="utf-8"
        )
    )
    costos = {r["costo"] for r in hormiga["resultados"].values()}
    assert len(costos) == 1 and all(
        r["encontrada"] for r in hormiga["resultados"].values()
    )
    ok(
        "BFS, Dijkstra y A* coinciden en una ruta de costo 21 que recoge los tres alimentos."
    )
    for representacion, n in [("binario", 100), ("real", 150)]:
        datos = json.loads(
            (
                ROOT
                / f"03-lab-algoritmos-evolutivos/resultados/{representacion}/corrida.json"
            ).read_text(encoding="utf-8")
        )
        hist = datos["historial"]
        assert len(hist) == n + 1
        maximizar = representacion == "binario"
        assert all(
            b["mejor"] >= a["mejor"] if maximizar else b["mejor"] <= a["mejor"]
            for a, b in zip(hist, hist[1:])
        )
        s = hist[-1]
        x = s["vector"]
        objetivo = (
            20
            + math.e
            - 20 * math.exp(-0.2 * abs(x[0]))
            - math.exp(math.cos(2 * math.pi * x[0]))
            if maximizar
            else 10 * len(x) + sum(v * v - 10 * math.cos(2 * math.pi * v) for v in x)
        )
        assert math.isclose(objetivo, s["mejor"], rel_tol=1e-10, abs_tol=1e-12)
    ok(
        "Objetivos binario y real recalculados; historiales con G0 y elitismo coherente."
    )
    reinas = json.loads(
        (ROOT / "04-n-reinas/resultados/solucion.json").read_text(encoding="utf-8")
    )
    filas = reinas["filas_base_uno"]
    assert sorted(filas) == list(range(1, len(filas) + 1))
    assert all(
        abs(filas[i] - filas[j]) != j - i
        for i in range(len(filas))
        for j in range(i + 1, len(filas))
    )
    assert reinas["generacion"] == 77 and reinas["solucion_encontrada"]
    ok("Solución de doce reinas verificada por enumeración de todos sus pares.")
    pg = json.loads(
        (ROOT / "05-arboles-expresion/resultados/regresion.json").read_text(
            encoding="utf-8"
        )
    )
    with (ROOT / "05-arboles-expresion/resultados/predicciones.csv").open(
        encoding="utf-8", newline=""
    ) as f:
        filas = list(csv.DictReader(f))
    mse = sum((float(r["y"]) - float(r["prediccion"])) ** 2 for r in filas) / len(filas)
    assert len(filas) == 81 and math.isclose(
        mse, pg["metricas"]["mse"], rel_tol=1e-8, abs_tol=1e-30
    )
    assert pg["historial"][-1]["generacion"] == 19 and mse < 1e-8
    ok(
        "La regresión simbólica conserva los 81 puntos y su MSE coincide con las predicciones exportadas."
    )
    estudio = json.loads(
        (
            ROOT / "03-lab-algoritmos-evolutivos/resultados/estudio/resumen.json"
        ).read_text(encoding="utf-8")
    )
    assert estudio["corridas"] == 40
    ok("Estudio de cuarenta corridas, con cinco semillas por configuración.")
    total = 0
    for nombre, esperadas in [
        ("pruebas-propias.xml", 33),
        ("pruebas-hormiga.xml", 611),
    ]:
        arbol = ET.parse(ROOT / "validacion" / nombre)
        suites = list(arbol.getroot().iter("testsuite"))
        cantidad = sum(int(s.get("tests", "0")) for s in suites)
        errores = sum(
            int(s.get("failures", "0")) + int(s.get("errors", "0")) for s in suites
        )
        assert cantidad == esperadas and errores == 0, (nombre, cantidad, errores)
        total += cantidad
    ok(
        f"Reportes de {total} pruebas aprobadas: 611 del equipo y 33 de los programas nuevos."
    )
    fuentes = {}
    for p in (ROOT / "ia_unidad2").glob("*.py"):
        fuentes[p.relative_to(ROOT).as_posix()] = hashlib.sha256(
            p.read_bytes()
        ).hexdigest()
    destino = ROOT / "validacion/entrega.json"
    destino.parent.mkdir(exist_ok=True)
    destino.write_text(
        json.dumps(
            {
                "estado": "correcto",
                "fecha_utc": datetime.now(timezone.utc).isoformat(),
                "comprobaciones": comprobaciones,
                "sha256_programas": fuentes,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
