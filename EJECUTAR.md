# Ejecutar las actividades

## En este equipo

Desde PowerShell en C:\Users\elias\Downloads\Said - github:

    .\.venv-u2\Scripts\python.exe .\Fundamentos_IA_Unidad_2\iniciar.py hormiga
    .\.venv-u2\Scripts\python.exe .\Fundamentos_IA_Unidad_2\iniciar.py laboratorio
    .\.venv-u2\Scripts\python.exe .\Fundamentos_IA_Unidad_2\iniciar.py reinas
    .\.venv-u2\Scripts\python.exe .\Fundamentos_IA_Unidad_2\iniciar.py arboles

El entorno de Python 3.12 está en .venv-u2, junto a la carpeta de la unidad. El visualizador de grafos está reservado y no tiene una aplicación todavía.

## Preparar otro equipo

Con Python 3.12 instalado, abre una terminal en la raíz de este repositorio:

    python -m venv .venv
    .\.venv\Scripts\python.exe -m pip install -r requirements.txt
    .\.venv\Scripts\python.exe iniciar.py laboratorio

Cambia laboratorio por hormiga, reinas o arboles. En Linux/macOS el ejecutable del entorno es .venv/bin/python. Se necesita una sesión gráfica para las ventanas.

Los archivos main.py de las secciones 03, 04 y 05 son accesos directos a las aplicaciones. Conserva la carpeta ia_unidad2 junto a ellas: contiene sus motores e interfaces.

## Resultados y evidencias

Cada aplicación puede guardar los datos de su corrida mediante su botón de exportación. Las demostraciones incluidas están en las carpetas resultados y las capturas en capturas.

Para repetir las demostraciones y actualizar las seis imágenes:

    .\.venv\Scripts\python.exe herramientas/generar_evidencias.py

El script ejecuta los motores, dibuja las ventanas Qt y captura sus widgets, sin crear reportes HTML. Su opción --visible muestra las ventanas durante la generación. Las operaciones de los programas son las mismas en ambos modos.

El estudio de comparación de representaciones se ejecuta con:

    .\.venv\Scripts\python.exe 03-lab-algoritmos-evolutivos/estudio.py

## Pruebas

    .\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
    .\.venv\Scripts\python.exe -m pytest -q

Para comprobar también el proyecto de la hormiga en su propio entorno de pruebas:

    .\.venv\Scripts\python.exe -m pip install --no-deps -e ./01-problema-hormiga
    .\.venv\Scripts\python.exe -m pytest -q -c 01-problema-hormiga/pyproject.toml 01-problema-hormiga/tests

En una sesión sin pantalla, establece QT_QPA_PLATFORM=offscreen antes de ejecutar las pruebas. El script herramientas/validar_entrega.py revisa además las rutas, los resultados, las capturas y la integridad del proyecto compartido.
