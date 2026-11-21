"""Árboles inmutables, intérprete restringido, CSV y programación genética."""

import ast
import csv
from dataclasses import dataclass
import math
from pathlib import Path
import random
import numpy as np

UNARIOS = (
    "sin",
    "cos",
    "tan",
    "sqrt",
    "log",
    "log10",
    "exp",
    "abs",
    "asin",
    "acos",
    "atan",
    "floor",
    "ceil",
    "neg",
)
BINARIOS = ("+", "-", "*", "/", "^")
FUNCIONES = {
    k: getattr(np, k)
    for k in (
        "sin",
        "cos",
        "tan",
        "sqrt",
        "log",
        "log10",
        "exp",
        "abs",
        "floor",
        "ceil",
    )
}
FUNCIONES.update(asin=np.arcsin, acos=np.arccos, atan=np.arctan)


@dataclass(frozen=True)
class Nodo:
    valor: str | float
    hijos: tuple = ()

    @property
    def altura(self):
        return 0 if not self.hijos else 1 + max(n.altura for n in self.hijos)

    @property
    def tamano(self):
        return 1 + sum(n.tamano for n in self.hijos)

    def texto(self):
        if not self.hijos:
            return self.valor if isinstance(self.valor, str) else f"{self.valor:g}"
        if len(self.hijos) == 1:
            return (
                f"(-{self.hijos[0].texto()})"
                if self.valor == "neg"
                else f"{self.valor}({self.hijos[0].texto()})"
            )
        return f"({self.hijos[0].texto()} {self.valor} {self.hijos[1].texto()})"


def interpretar(texto):
    if len(texto) > 2000:
        raise ValueError("La expresión es demasiado larga.")
    try:
        fuente = ast.parse(texto.replace("^", "**"), mode="eval")
    except (SyntaxError, RecursionError) as e:
        raise ValueError(
            "Expresión no válida; utiliza multiplicación explícita, como 2*x."
        ) from e
    operadores = {ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/", ast.Pow: "^"}

    def convertir(n, nivel=0):
        if nivel > 12:
            raise ValueError("El árbol supera doce niveles.")
        if isinstance(n, ast.Constant) and type(n.value) in (int, float):
            try:
                valor = float(n.value)
            except (OverflowError, ValueError) as e:
                raise ValueError("Constante fuera de rango.") from e
            if not math.isfinite(valor):
                raise ValueError("Las constantes deben ser finitas.")
            return Nodo(valor)
        if isinstance(n, ast.Name) and n.id in {"x", "pi", "e"}:
            return Nodo("x" if n.id == "x" else math.pi if n.id == "pi" else math.e)
        if isinstance(n, ast.BinOp) and type(n.op) in operadores:
            return Nodo(
                operadores[type(n.op)],
                (convertir(n.left, nivel + 1), convertir(n.right, nivel + 1)),
            )
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.UAdd, ast.USub)):
            hijo = convertir(n.operand, nivel + 1)
            return hijo if isinstance(n.op, ast.UAdd) else Nodo("neg", (hijo,))
        if (
            isinstance(n, ast.Call)
            and isinstance(n.func, ast.Name)
            and not n.keywords
            and len(n.args) == 1
        ):
            nombre = "log" if n.func.id == "ln" else n.func.id
            if nombre in UNARIOS and nombre != "neg":
                return Nodo(nombre, (convertir(n.args[0], nivel + 1),))
        raise ValueError(
            "Solo se permiten x, constantes, operadores matemáticos y funciones del catálogo."
        )

    raiz = convertir(fuente.body)
    if raiz.tamano > 127:
        raise ValueError("El árbol supera 127 nodos.")
    return raiz


def evaluar(raiz, x, protegido=False):
    xs = np.asarray(x, dtype=float)

    def rec(n):
        if not n.hijos:
            return (
                xs.copy()
                if n.valor == "x"
                else np.full_like(xs, float(n.valor), dtype=float)
            )
        v = [rec(h) for h in n.hijos]
        if n.valor == "+":
            return v[0] + v[1]
        if n.valor == "-":
            return v[0] - v[1]
        if n.valor == "*":
            return v[0] * v[1]
        if n.valor == "/":
            if protegido:
                resultado = np.ones_like(v[0])
                np.divide(v[0], v[1], out=resultado, where=np.abs(v[1]) > 1e-12)
                return resultado
            if np.any(np.abs(v[1]) <= 1e-12):
                raise ValueError("División entre cero.")
            return v[0] / v[1]
        if n.valor == "^":
            if np.any(np.abs(v[1]) > 64):
                raise ValueError("El exponente excede el límite numérico 64.")
            return np.power(v[0], v[1])
        if n.valor == "neg":
            return -v[0]
        if protegido and n.valor == "sqrt":
            return np.sqrt(np.abs(v[0]))
        if protegido and n.valor in {"log", "log10"}:
            return FUNCIONES[n.valor](np.maximum(np.abs(v[0]), 1e-12))
        return FUNCIONES[n.valor](v[0])

    with np.errstate(over="raise", invalid="raise", divide="raise", under="ignore"):
        try:
            resultado = rec(raiz)
        except (FloatingPointError, OverflowError, ZeroDivisionError) as e:
            raise ValueError(
                "La expresión no está definida en todos los puntos."
            ) from e
    if not np.all(np.isfinite(resultado)):
        raise ValueError("La evaluación produjo valores no finitos.")
    return resultado


def curva(raiz, x, protegido=False):
    try:
        return evaluar(raiz, x, protegido)
    except ValueError:
        salida = []
        for valor in x:
            try:
                salida.append(float(evaluar(raiz, valor, protegido)))
            except ValueError:
                salida.append(float("nan"))
        return np.array(salida)


def metricas(observado, predicho):
    y = np.asarray(observado, dtype=float)
    p = np.asarray(predicho, dtype=float)
    if (
        y.shape != p.shape
        or y.size == 0
        or not np.all(np.isfinite(y))
        or not np.all(np.isfinite(p))
    ):
        raise ValueError("Las métricas requieren pares finitos y del mismo tamaño.")
    with np.errstate(over="raise", invalid="raise", divide="raise", under="ignore"):
        try:
            mse = float(np.mean((y - p) ** 2))
            var = float(np.mean((y - y.mean()) ** 2))
        except FloatingPointError as e:
            raise ValueError("Los errores exceden el rango numérico.") from e
    return {
        "mse": mse,
        "rmse": math.sqrt(mse),
        "nmse": mse / var if var > 0 else None,
        "r2": 1 - mse / var if var > 0 else None,
        "n": int(y.size),
    }


def leer_csv(ruta):
    with Path(ruta).open(encoding="utf-8-sig", newline="") as f:
        contenido = f.read()
    lineas = [linea for linea in contenido.splitlines() if linea.strip()]
    if not lineas:
        raise ValueError("El CSV está vacío.")
    delimitador = ";" if ";" in lineas[0] else ","
    filas = list(csv.reader(lineas, delimiter=delimitador))
    xs = []
    ys = []
    if [s.strip().lower() for s in filas[0]] == ["x", "y"]:
        filas = filas[1:]
    for numero, fila in enumerate(filas, 1):
        if len(fila) != 2:
            raise ValueError(
                f"Fila {numero}: se necesitan exactamente dos columnas x,y."
            )
        try:
            x, y = (
                float(s.strip().replace(",", "."))
                if delimitador == ";"
                else float(s.strip())
                for s in fila
            )
        except ValueError as e:
            raise ValueError(f"Fila {numero}: valor no numérico.") from e
        if not math.isfinite(x) or not math.isfinite(y):
            raise ValueError(f"Fila {numero}: valores no finitos.")
        xs.append(x)
        ys.append(y)
    if not xs:
        raise ValueError("El CSV no tiene observaciones.")
    if len(xs) > 10000:
        raise ValueError("Se admiten hasta 10 000 observaciones.")
    return np.array(xs), np.array(ys)


def recorridos(raiz, modo="Preorden"):
    salida = []

    def rec(n, ruta):
        if modo == "Preorden":
            salida.append((ruta, n))
        if n.hijos:
            rec(n.hijos[0], ruta + (0,))
        if modo == "Inorden":
            salida.append((ruta, n))
        if len(n.hijos) > 1:
            rec(n.hijos[1], ruta + (1,))
        if modo == "Postorden":
            salida.append((ruta, n))

    rec(raiz, ())
    return salida


def rutas(raiz):
    return [ruta for ruta, n in recorridos(raiz)]


def obtener(raiz, ruta):
    for indice in ruta:
        raiz = raiz.hijos[indice]
    return raiz


def sustituir(raiz, ruta, nueva):
    if not ruta:
        return nueva
    hijos = list(raiz.hijos)
    hijos[ruta[0]] = sustituir(hijos[ruta[0]], ruta[1:], nueva)
    return Nodo(raiz.valor, tuple(hijos))


def aleatorio(rng, altura, operadores=("+", "-", "*", "sin", "cos"), completo=False):
    if altura <= 0 or (not completo and rng.random() < 0.32):
        return Nodo(
            "x"
            if rng.random() < 0.6
            else rng.choice([-3.0, -2.0, -1.0, 0.0, 0.5, 1.0, 2.0, 3.0])
        )
    op = rng.choice(operadores)
    return Nodo(
        op,
        tuple(
            aleatorio(rng, altura - 1, operadores, completo)
            for _ in range(2 if op in BINARIOS else 1)
        ),
    )


@dataclass(frozen=True)
class ConfiguracionPG:
    poblacion: int = 100
    generaciones: int = 100
    altura: int = 4
    prob_cruce: float = 0.85
    prob_mutacion: float = 0.25
    elites: int = 2
    seleccion: str = "Torneo"
    mutaciones: tuple = ("Hojas", "Operadores", "Intercambio", "Subárbol")
    operadores: tuple = ("+", "-", "*", "sin", "cos")
    semilla: int = 2430085
    tolerancia: float = 1e-8
    protegido: bool = False

    def validar(self):
        if not 8 <= self.poblacion <= 300 or not 0 <= self.generaciones <= 500:
            raise ValueError("Población 8–300; generaciones 0–500.")
        if not 1 <= self.altura <= 6:
            raise ValueError(
                "El nivel máximo debe estar entre 1 y 6; la raíz está en nivel 0."
            )
        if not 0 <= self.elites < self.poblacion:
            raise ValueError("Elitismo fuera de rango.")
        if not 0 <= self.prob_cruce <= 1 or not 0 <= self.prob_mutacion <= 1:
            raise ValueError("Probabilidades entre 0 y 1.")
        if not self.operadores or any(
            op not in BINARIOS + UNARIOS for op in self.operadores
        ):
            raise ValueError("Catálogo de operadores no válido.")
        if not set(self.mutaciones) <= set(
            ("Hojas", "Operadores", "Intercambio", "Subárbol")
        ):
            raise ValueError("Mutación desconocida.")
        if self.seleccion not in {"Torneo", "Ruleta"}:
            raise ValueError("Selección desconocida.")
        if not math.isfinite(self.tolerancia) or self.tolerancia < 0:
            raise ValueError("Tolerancia no válida.")


class MotorPG:
    def __init__(self, x, y, config=ConfiguracionPG()):
        config.validar()
        self.x = np.asarray(x, dtype=float)
        self.y = np.asarray(y, dtype=float)
        if (
            self.x.shape != self.y.shape
            or self.x.ndim != 1
            or self.x.size < 2
            or not np.all(np.isfinite(self.x))
            or not np.all(np.isfinite(self.y))
        ):
            raise ValueError("La evolución requiere al menos dos pares x,y finitos.")
        self.config = config
        self.rng = random.Random(config.semilla)
        self.numero = 0
        self.historial = []
        self.poblacion = [
            aleatorio(
                self.rng, 1 + i % config.altura, config.operadores, completo=i % 2 == 0
            )
            for i in range(config.poblacion)
        ]
        self.registrar([])

    def adaptar(self, arbol):
        try:
            return metricas(self.y, evaluar(arbol, self.x, self.config.protegido))
        except (ValueError, TypeError):
            return {
                "mse": float("inf"),
                "rmse": float("inf"),
                "nmse": None,
                "r2": None,
                "n": len(self.x),
            }

    def registrar(self, operaciones):
        self.metricas = [self.adaptar(n) for n in self.poblacion]
        self.orden = sorted(
            range(len(self.poblacion)),
            key=lambda i: (self.metricas[i]["mse"], self.poblacion[i].tamano),
        )
        idx = self.orden[0]
        s = {
            "generacion": self.numero,
            "arbol": self.poblacion[idx],
            "metricas": self.metricas[idx],
            "validos": sum(math.isfinite(m["mse"]) for m in self.metricas),
            "operaciones": operaciones,
        }
        self.historial.append(s)
        return s

    @property
    def terminado(self):
        return (
            self.numero >= self.config.generaciones
            or self.historial[-1]["metricas"]["mse"] <= self.config.tolerancia
        )

    def padre(self):
        if self.config.seleccion == "Torneo":
            candidatos = self.rng.sample(range(len(self.poblacion)), 3)
            return min(
                candidatos,
                key=lambda i: (self.metricas[i]["mse"], self.poblacion[i].tamano),
            )
        pesos = [1 / (1 + m["mse"]) for m in self.metricas]
        if not sum(pesos):
            return self.rng.randrange(len(self.poblacion))
        return self.rng.choices(range(len(self.poblacion)), weights=pesos, k=1)[0]

    def admisible(self, n):
        return n.altura <= self.config.altura and n.tamano <= 127

    def cruzar(self, p, q):
        a = self.rng.choice(rutas(p))
        b = self.rng.choice(rutas(q))
        nuevo = sustituir(p, a, obtener(q, b))
        return (nuevo, True) if self.admisible(nuevo) else (p, False)

    def mutar(self, p):
        tipo = self.rng.choice(self.config.mutaciones)
        candidatos = rutas(p)
        r = self.rng
        if tipo == "Hojas":
            candidatos = [a for a in candidatos if not obtener(p, a).hijos]
        if tipo == "Operadores":
            candidatos = [a for a in candidatos if obtener(p, a).hijos]
        if tipo == "Intercambio":
            candidatos = [a for a in candidatos if len(obtener(p, a).hijos) == 2]
        if not candidatos:
            return p, tipo + " (sin nodo compatible)"
        ruta = r.choice(candidatos)
        n = obtener(p, ruta)
        if tipo == "Hojas":
            nuevo = aleatorio(r, 0, self.config.operadores)
        elif tipo == "Operadores":
            posibles = [
                op
                for op in self.config.operadores
                if (2 if op in BINARIOS else 1) == len(n.hijos)
            ]
            nuevo = Nodo(r.choice(posibles), n.hijos) if posibles else n
        elif tipo == "Intercambio":
            nuevo = Nodo(n.valor, (n.hijos[1], n.hijos[0]))
        else:
            nuevo = aleatorio(r, self.config.altura - len(ruta), self.config.operadores)
        resultado = sustituir(p, ruta, nuevo)
        return (
            (resultado, tipo)
            if self.admisible(resultado)
            else (p, tipo + " (límite de tamaño)")
        )

    def paso(self):
        if self.terminado:
            return self.historial[-1]
        c = self.config
        nueva = [self.poblacion[i] for i in self.orden[: c.elites]]
        operaciones = []
        while len(nueva) < c.poblacion:
            p, q = self.poblacion[self.padre()], self.poblacion[self.padre()]
            hijo = p
            cruzado = False
            mutacion = "Sin mutación"
            if self.rng.random() < c.prob_cruce:
                hijo, cruzado = self.cruzar(p, q)
            if c.mutaciones and self.rng.random() < c.prob_mutacion:
                hijo, mutacion = self.mutar(hijo)
            if len(operaciones) < 5:
                operaciones.append(
                    {
                        "padre": p.texto(),
                        "donante": q.texto(),
                        "cruce_aplicado": cruzado,
                        "mutacion": mutacion,
                        "hijo": hijo.texto(),
                    }
                )
            nueva.append(hijo)
        self.poblacion = nueva
        self.numero += 1
        return self.registrar(operaciones)

    def ejecutar(self):
        while not self.terminado:
            self.paso()
        return self.historial[-1]
