import itertools
import math
import random
from dataclasses import replace
import numpy as np
import pytest
from ia_unidad2.optimizacion import (
    Configuracion,
    MotorGenetico,
    PROBLEMAS,
    probabilidades,
    seleccionar,
)
from ia_unidad2.reinas import (
    MotorReinas,
    ConfiguracionReinas,
    ataques,
    cruce_orden,
    cruce_ciclos,
)
from ia_unidad2.expresiones import (
    interpretar,
    evaluar,
    metricas,
    leer_csv,
    recorridos,
    MotorPG,
    ConfiguracionPG,
)


def test_extremos_de_codificacion_y_funciones():
    c = Configuracion(
        problema="Máximo oscilatorio",
        representacion="Binaria",
        dimensiones=1,
        cruce="Monopunto",
    )
    m = MotorGenetico(c)
    assert m.decodificar((0,) * c.bits()) == (0.0,)
    assert m.decodificar((1,) * c.bits()) == (32.0,)
    assert 32 / (2 ** c.bits() - 1) <= c.precision
    assert PROBLEMAS["Esfera"].evaluar((0, 0, 0)) == 0
    assert PROBLEMAS["Rastrigin"].evaluar((0, 0)) == 0
    assert PROBLEMAS["Schwefel acotada"].evaluar((0,)) == 0


@pytest.mark.parametrize(
    "representacion,cruce",
    [("Binaria", "Monopunto")]
    + [("Real", x) for x in ["Monopunto", "Uniforme", "Aritmético", "SBX"]],
)
def test_optimizar_conserva_dominios_elites_y_poblacion_impar(representacion, cruce):
    c = Configuracion(
        representacion=representacion,
        cruce=cruce,
        poblacion=25,
        generaciones=15,
        semilla=31,
    )
    m = MotorGenetico(c)
    m.ejecutar()
    assert len(m.historial) == 16
    assert all(b["mejor"] <= a["mejor"] for a, b in zip(m.historial, m.historial[1:]))
    for s in m.historial:
        assert len(s["poblacion"]) == 25
        assert all(-5.12 <= v <= 5.12 for g in s["poblacion"] for v in m.decodificar(g))
    r = MotorGenetico(c)
    r.ejecutar()
    assert m.historial == r.historial


def test_seleccion_con_objetivos_negativos_y_empates():
    for maximizar in [True, False]:
        p = probabilidades([-50, -10, 0], maximizar)
        assert all(v > 0 for v in p) and sum(p) == pytest.approx(1)
        assert p[2] > p[0] if maximizar else p[0] > p[2]
    assert probabilidades([3, 3, 3]) == [1 / 3] * 3
    elegidos = seleccionar([0, 5, 10], 10000, random.Random(1), "SUS")
    assert elegidos.count(0) > elegidos.count(1) > elegidos.count(2)


def test_maximizacion_y_validacion_de_parametros():
    c = Configuracion(
        problema="Máximo oscilatorio",
        dimensiones=1,
        representacion="Binaria",
        cruce="Monopunto",
        generaciones=60,
    )
    m = MotorGenetico(c)
    inicial = m.historial[0]["mejor"]
    final = m.ejecutar()
    assert inicial <= final["mejor"] < 23
    for cambio in [
        {"elites": 80},
        {"precision": 0},
        {"dimensiones": 2},
        {"poblacion": 1},
        {"prob_mutacion": float("nan")},
    ]:
        with pytest.raises(ValueError):
            MotorGenetico(replace(c, **cambio))


def test_oraculo_exhaustivo_cuatro_reinas():
    soluciones = [g for g in itertools.permutations(range(4)) if not ataques(g)]
    assert set(soluciones) == {(1, 3, 0, 2), (2, 0, 3, 1)}
    assert len(ataques(tuple(range(8)))) == 28
    with pytest.raises(ValueError):
        ataques((0, 0, 1, 2))


@pytest.mark.parametrize("cruzador", [cruce_orden, cruce_ciclos])
def test_cruces_de_permutacion_no_pierden_reinas(cruzador):
    r = random.Random(81)
    for n in range(1, 15):
        for _ in range(25):
            p = tuple(r.sample(range(n), n))
            q = tuple(r.sample(range(n), n))
            assert sorted(cruzador(p, q, r)) == list(range(n))


def test_reinas_busqueda_real_y_casos_imposibles():
    m = MotorReinas(ConfiguracionReinas(n=12, poblacion=100, semilla=2430085))
    fin = m.ejecutar()
    assert fin["mejor"] == 0 and not ataques(fin["genes"])
    assert m.numero > 0
    for n in [2, 3]:
        imposible = MotorReinas(ConfiguracionReinas(n=n, generaciones=10))
        assert imposible.ejecutar()["mejor"] > 0 and imposible.numero == 10


@pytest.mark.parametrize(
    "texto,valor",
    [
        ("2^3^2", 512),
        ("-2^2", -4),
        ("(-2)^2", 4),
        ("sin(pi/2)", 1),
        ("ln(e)", 1),
        ("1e-3", 0.001),
    ],
)
def test_parser_contra_resultados_conocidos(texto, valor):
    assert float(evaluar(interpretar(texto), 0)) == pytest.approx(valor)


@pytest.mark.parametrize(
    "texto",
    [
        "__import__('os')",
        "x.__class__",
        "open('archivo')",
        "[1,2]",
        "x[0]",
        "sin(x,y)",
        "lambda x: x",
        "1e999",
    ],
)
def test_parser_rechaza_codigo_ajeno_al_lenguaje(texto):
    with pytest.raises(ValueError):
        interpretar(texto)


def test_dominios_y_evaluacion_protegida_no_ignoran_puntos():
    arbol = interpretar("sqrt(x)")
    with pytest.raises(ValueError):
        evaluar(arbol, [-1, 0, 1])
    assert np.array_equal(evaluar(arbol, [-1, 0, 1], True), [1, 0, 1])
    with pytest.raises(ValueError):
        evaluar(interpretar("1/x"), [0, 1])
    assert np.array_equal(evaluar(interpretar("1/x"), [0, 1], True), [1, 1])
    m = MotorPG(
        np.array([-1, 0, 1]), np.array([1, 0, 1]), ConfiguracionPG(generaciones=0)
    )
    assert math.isinf(m.adaptar(arbol)["mse"])


def test_metricas_y_csv_estricto(tmp_path):
    m = metricas([1, 2, 3], [1, 2, 4])
    assert m["mse"] == pytest.approx(1 / 3) and m["r2"] == pytest.approx(0.5)
    assert metricas([3, 3], [3, 3])["r2"] is None
    archivo = tmp_path / "datos.csv"
    archivo.write_text("\ufeffx;y\n1,5;2,5\n2;4\n", encoding="utf-8")
    x, y = leer_csv(archivo)
    assert x.tolist() == [1.5, 2] and y.tolist() == [2.5, 4]
    archivo.write_text("x,y\n1,2\n2,NO\n", encoding="utf-8")
    with pytest.raises(ValueError):
        leer_csv(archivo)


def test_recorridos_y_regresion_reproducible():
    t = interpretar("(x+1)*2")
    assert [n.valor for r, n in recorridos(t, "Preorden")] == ["*", "+", "x", 1.0, 2.0]
    assert [n.valor for r, n in recorridos(t, "Postorden")] == ["x", 1.0, "+", 2.0, "*"]
    x = np.linspace(-2, 2, 41)
    y = x * x + x + 1
    c = ConfiguracionPG(generaciones=50)
    a = MotorPG(x, y, c)
    b = MotorPG(x, y, c)
    s = a.ejecutar()
    otro = b.ejecutar()
    assert s["metricas"] == otro["metricas"] and s["arbol"] == otro["arbol"]
    assert s["metricas"]["mse"] < 1e-6
    assert np.allclose(evaluar(s["arbol"], x), y, atol=0.001)
    assert all(
        h["arbol"].altura <= c.altura and h["arbol"].tamano <= 127 for h in a.historial
    )
