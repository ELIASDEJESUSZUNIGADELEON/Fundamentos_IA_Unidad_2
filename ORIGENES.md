# Procedencia de los proyectos

## Proyecto compartido de la hormiga

La sección 01 es el proyecto del equipo proporcionado por César, conservado con su autoría original en pyproject.toml.

- Repositorio: https://github.com/cesar-upv/2430233_FUNDAMENTOS_IA_UNIDAD_2
- Revisión: 0d10fb6d0704d2e3419de5a61a8adba6e660f5a7
- Carpeta: 01-problema-hormiga.
- Se conservaron 63 archivos de aplicación, pruebas y documentación. Los ajustes de agentes de desarrollo y su registro de conversación no se incorporaron.
- [Registro de integridad](herramientas/origen_hormiga.json): SHA-256 de los archivos recibidos.
- resultados/verificacion_equipo.json y la captura de la unidad se generaron al ejecutar el proyecto en este equipo.

## Programas propios de las secciones 03, 04 y 05

Los motores y las interfaces de ia_unidad2 se implementaron para esta unidad. Se consultaron los temas y el comportamiento descrito en los README de:

- https://github.com/ZapataFrame/FIA-Actividades-Unidad-2/tree/54cb02ffaf5aac71bf4b64715a944a65a4035a3d/03-algoritmos-geneticos
- https://github.com/cesar-upv/2430233_FUNDAMENTOS_IA_UNIDAD_2/tree/0d10fb6d0704d2e3419de5a61a8adba6e660f5a7

No se importó el código ni las capturas de esos proyectos para las secciones 03–05. Las interfaces tienen una distribución propia: parámetros superiores con población lateral en el laboratorio, tablero con controles derechos en N reinas, y árbol/curva con herramientas inferiores en expresiones.

Las funciones de optimización se identifican por su fórmula en la documentación. No se afirma una reproducción exacta de todas las variantes del libro citado en los repositorios; el alcance ejecutable de cada programa está descrito en su README.

## Dependencias

PySide6 proporciona los widgets; Matplotlib dibuja las gráficas; NumPy realiza los cálculos vectoriales de expresiones. La selección, reproducción, mutación, codificación y bucles de evolución están implementados en el código de la unidad, sin una biblioteca que ejecute el algoritmo genético.

Las fuentes utilizadas para las capturas de Windows se cargan desde las fuentes instaladas del sistema. No se incluyen archivos de fuentes externos. Las capturas se obtienen de las ventanas Qt y no de páginas HTML.
