"""Lanzador común. Ejemplo: python iniciar.py laboratorio."""

import argparse
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser(
        description="Actividades de Fundamentos de IA · Unidad 2"
    )
    parser.add_argument(
        "actividad", choices=["hormiga", "laboratorio", "reinas", "arboles"]
    )
    args = parser.parse_args()
    if args.actividad == "hormiga":
        sys.path.insert(0, str(Path(__file__).parent / "01-problema-hormiga/src"))
        from ant_pathfinding import main as hormiga

        return hormiga()
    from ia_unidad2.interfaz_comun import preparar_app

    app = preparar_app()
    if args.actividad == "laboratorio":
        from ia_unidad2.ventana_laboratorio import Laboratorio

        ventana = Laboratorio()
    elif args.actividad == "reinas":
        from ia_unidad2.ventana_reinas import VentanaReinas

        ventana = VentanaReinas()
    else:
        from ia_unidad2.ventana_arboles import VentanaArboles

        ventana = VentanaArboles()
    ventana.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
