from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ia_unidad2.interfaz_comun import preparar_app
from ia_unidad2.ventana_arboles import VentanaArboles

if __name__ == "__main__":
    app = preparar_app()
    ventana = VentanaArboles()
    ventana.show()
    raise SystemExit(app.exec())
