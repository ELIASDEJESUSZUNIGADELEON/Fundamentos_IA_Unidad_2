"""Comparación reproducible de configuraciones completas, con cinco semillas."""

from pathlib import Path
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ia_unidad2.optimizacion import Configuracion, MotorGenetico
from ia_unidad2.interfaz_comun import guardar_csv, guardar_json


def main():
    filas = []
    for problema in [
        "Máximo oscilatorio",
        "Mínimo oscilatorio",
        "Schwefel acotada",
        "Rastrigin",
    ]:
        dimensiones = (
            1 if problema in {"Máximo oscilatorio", "Mínimo oscilatorio"} else 3
        )
        for representacion in ["Binaria", "Real"]:
            for semilla in range(5):
                c = Configuracion(
                    problema=problema,
                    representacion=representacion,
                    dimensiones=dimensiones,
                    poblacion=60,
                    generaciones=100,
                    semilla=semilla,
                    cruce="Monopunto" if representacion == "Binaria" else "SBX",
                    prob_mutacion=0.01 if representacion == "Binaria" else 0.04,
                )
                comienzo = time.perf_counter()
                m = MotorGenetico(c)
                s = m.ejecutar()
                filas.append(
                    [
                        problema,
                        representacion,
                        dimensiones,
                        semilla,
                        c.cruce,
                        c.prob_mutacion,
                        s["mejor"],
                        s["vector"],
                        time.perf_counter() - comienzo,
                    ]
                )
    salida = Path(__file__).parent / "resultados/estudio"
    guardar_csv(
        salida / "corridas.csv",
        [
            "problema",
            "representacion",
            "dimensiones",
            "semilla",
            "cruce",
            "p_mutacion",
            "mejor",
            "vector",
            "segundos",
        ],
        filas,
    )
    resumen = []
    for problema in dict.fromkeys(r[0] for r in filas):
        for representacion in ["Binaria", "Real"]:
            valores = [
                r[6] for r in filas if r[0] == problema and r[1] == representacion
            ]
            resumen.append(
                {
                    "problema": problema,
                    "representacion": representacion,
                    "corridas": len(valores),
                    "media": statistics.fmean(valores),
                    "desviacion": statistics.pstdev(valores),
                }
            )
    guardar_json(
        salida / "resumen.json",
        {
            "corridas": len(filas),
            "nota": "Se comparan configuraciones completas: cambian representación, cruce y unidad/probabilidad de mutación. No se atribuyen las diferencias solo a la codificación.",
            "resultados": resumen,
        },
    )
    print(
        f"Estudio guardado: {len(filas)} corridas con cinco semillas por configuración."
    )
    for r in resumen:
        print(
            f"{r['problema']} / {r['representacion']}: {r['media']:.6g} ± {r['desviacion']:.4g}"
        )


if __name__ == "__main__":
    main()
