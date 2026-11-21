# Procedencia de los proyectos

## Proyecto compartido de la hormiga

La sección 01 es el proyecto del equipo proporcionado por César, conservado con su autoría original en pyproject.toml.

Equipo: Elias de Jesus Zuñiga de Leon, **César Euresti** y **Junior Arturo Vazquez Leonel**.

- Repositorio: https://github.com/cesar-upv/2430233_FUNDAMENTOS_IA_UNIDAD_2
- Revisión: 0d10fb6d0704d2e3419de5a61a8adba6e660f5a7
- Carpeta: 01-problema-hormiga.
- Se conservaron 63 archivos de aplicación, pruebas y documentación. Los ajustes de agentes de desarrollo y su registro de conversación no se incorporaron.
- [Registro de integridad](herramientas/origen_hormiga.json): SHA-256 de los archivos recibidos.
- resultados/verificacion_equipo.json y la captura de la unidad se generaron al ejecutar el proyecto en este equipo.

El README de la actividad se amplió únicamente para identificar al equipo. El registro conserva tanto la huella original como la del documento actualizado.

## Proyecto compartido del visualizador de grafos

Equipo: Elias de Jesus Zuñiga de Leon y **Osvaldo Fabian Ramiro Balboa**.

- Repositorio: https://github.com/FabiRamiro/Algoritmos-Said
- Revisión: 1c02cdb4ad966b2832107ac405bd517d02bae674.
- Carpeta: 02-visualizador-de-grafos.
- Se incorporaron 60 archivos de aplicación, datos, pruebas y documentación. Se omitieron cachés, capturas y exportaciones anteriores, y los videos MP4 opcionales.
- [Registro de integridad y ajustes locales](herramientas/origen_grafos.json).
- Se añadieron créditos al README, identificadores únicos a las sesiones de capturas para evitar colisiones y el backend multimedia nativo en Windows tras comprobar un fallo de FFmpeg con un archivo dañado. Los motores de los cuatro algoritmos se conservan.
- La captura y resultados/verificacion_equipo.json se generaron con la aplicación integrada: los cuatro algoritmos obtuvieron 13 → 16 → 17 → 69, con costo 14.

## Programas propios de las secciones 03, 04 y 05

Los motores y las interfaces de ia_unidad2 se implementaron para esta unidad. Se consultaron los temas y el comportamiento descrito en los README de:

- https://github.com/ZapataFrame/FIA-Actividades-Unidad-2/tree/54cb02ffaf5aac71bf4b64715a944a65a4035a3d/03-algoritmos-geneticos
- https://github.com/cesar-upv/2430233_FUNDAMENTOS_IA_UNIDAD_2/tree/0d10fb6d0704d2e3419de5a61a8adba6e660f5a7

No se importó el código ni las capturas de esos proyectos para las secciones 03–05. Las interfaces tienen una distribución propia: parámetros superiores con población lateral en el laboratorio, tablero con controles derechos en N reinas, y árbol/curva con herramientas inferiores en expresiones.

Las funciones de optimización se identifican por su fórmula en la documentación. No se afirma una reproducción exacta de todas las variantes del libro citado en los repositorios; el alcance ejecutable de cada programa está descrito en su README.

## Dependencias

PySide6 proporciona los widgets; Matplotlib dibuja las gráficas; NumPy realiza los cálculos vectoriales de expresiones. La selección, reproducción, mutación, codificación y bucles de evolución están implementados en el código de la unidad, sin una biblioteca que ejecute el algoritmo genético.

Las fuentes utilizadas para las capturas de Windows se cargan desde las fuentes instaladas del sistema. No se incluyen archivos de fuentes externos. Las capturas se obtienen de las ventanas Qt y no de páginas HTML.
