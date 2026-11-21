"""Algoritmo genético binario/real independiente de la interfaz."""

from dataclasses import dataclass
import math
import random
from statistics import fmean, pstdev


@dataclass(frozen=True)
class Problema:
    nombre: str
    formula: str
    dominio: tuple[float, float]
    maximizar: bool = False
    dimensiones_fijas: int | None = None

    def evaluar(self, x):
        if self.nombre == "Máximo oscilatorio":
            a = x[0]
            return (
                20
                + math.e
                - 20 * math.exp(-0.2 * abs(a))
                - math.exp(math.cos(2 * math.pi * a))
            )
        if self.nombre == "Mínimo oscilatorio":
            a = x[0]
            return -abs(a * math.sin(math.sqrt(abs(a))))
        if self.nombre == "Schwefel acotada":
            return sum(-a * math.sin(math.sqrt(abs(a))) for a in x)
        if self.nombre == "Rastrigin":
            return 10 * len(x) + sum(a * a - 10 * math.cos(2 * math.pi * a) for a in x)
        return sum(a * a for a in x)


PROBLEMAS = {
    p.nombre: p
    for p in [
        Problema(
            "Máximo oscilatorio",
            "20 + e − 20 exp(−0.2|x|) − exp(cos(2πx))",
            (0, 32),
            True,
            1,
        ),
        Problema("Mínimo oscilatorio", "−|x sen(√|x|)|", (-250, 250), False, 1),
        Problema("Schwefel acotada", "Σ −xi sen(√|xi|)", (0, 100)),
        Problema("Rastrigin", "10n + Σ (xi² − 10 cos(2πxi))", (-5.12, 5.12)),
        Problema("Esfera", "Σ xi²", (-5, 5)),
    ]
}


@dataclass(frozen=True)
class Configuracion:
    problema: str = "Rastrigin"
    representacion: str = "Real"
    dimensiones: int = 2
    poblacion: int = 80
    generaciones: int = 120
    precision: float = 0.001
    seleccion: str = "Torneo"
    cruce: str = "SBX"
    prob_cruce: float = 0.85
    prob_mutacion: float = 0.04
    elites: int = 2
    semilla: int = 2430085
    alfa: float = 0.5
    eta: float = 5

    def validar(self):
        if self.problema not in PROBLEMAS:
            raise ValueError("Elige una función del catálogo.")
        if self.representacion not in {"Binaria", "Real"}:
            raise ValueError("Representación desconocida.")
        if not 1 <= self.dimensiones <= 8:
            raise ValueError("Dimensiones: entre 1 y 8.")
        fijas = PROBLEMAS[self.problema].dimensiones_fijas
        if fijas and self.dimensiones != fijas:
            raise ValueError("Esta función utiliza una sola variable.")
        if not 4 <= self.poblacion <= 400:
            raise ValueError("Población: entre 4 y 400.")
        if not 0 <= self.generaciones <= 1000:
            raise ValueError("Generaciones: entre 0 y 1000.")
        if self.poblacion * (self.generaciones + 1) > 120_000:
            raise ValueError(
                "Reduce población o generaciones para conservar el historial."
            )
        if not 0 <= self.elites < self.poblacion:
            raise ValueError("Las élites deben ser menores que la población.")
        if not all(
            math.isfinite(p) and 0 <= p <= 1
            for p in [self.prob_cruce, self.prob_mutacion, self.alfa]
        ):
            raise ValueError("Las probabilidades y alfa deben estar entre 0 y 1.")
        if not math.isfinite(self.eta) or self.eta <= 0:
            raise ValueError("Eta debe ser positiva.")
        if not math.isfinite(self.precision) or self.precision <= 0:
            raise ValueError("La precisión debe ser positiva.")
        if self.seleccion not in {"Torneo", "Ruleta", "SUS"}:
            raise ValueError("Selección desconocida.")
        if self.cruce not in {"Monopunto", "Uniforme", "Aritmético", "SBX"}:
            raise ValueError("Cruce desconocido.")
        if self.representacion == "Binaria" and self.cruce != "Monopunto":
            raise ValueError("La representación binaria usa cruce monopunto.")
        if self.bits() > 40:
            raise ValueError("La precisión exige más de 40 bits por variable.")

    def bits(self):
        a, b = PROBLEMAS[self.problema].dominio
        return max(1, math.ceil(math.log2((b - a) / self.precision + 1)))


def probabilidades(valores, maximizar=False):
    lo, hi = min(valores), max(valores)
    if lo == hi:
        return [1 / len(valores)] * len(valores)
    base = 0.01 * (hi - lo)
    pesos = [(v - lo if maximizar else hi - v) + base for v in valores]
    total = sum(pesos)
    return [p / total for p in pesos]


def seleccionar(valores, n, rng, metodo, maximizar=False):
    if metodo == "Torneo":
        return [
            min(
                rng.sample(range(len(valores)), min(3, len(valores))),
                key=lambda i: -valores[i] if maximizar else valores[i],
            )
            for _ in range(n)
        ]
    pesos = probabilidades(valores, maximizar)
    if metodo == "Ruleta":
        return rng.choices(range(len(valores)), weights=pesos, k=n)
    inicio = rng.random() / n
    acumulado = pesos[0]
    i = 0
    elegidos = []
    for j in range(n):
        punto = inicio + j / n
        while punto > acumulado and i < len(pesos) - 1:
            i += 1
            acumulado += pesos[i]
        elegidos.append(i)
    return elegidos


class MotorGenetico:
    def __init__(self, config=Configuracion()):
        config.validar()
        self.config = config
        self.problema = PROBLEMAS[config.problema]
        self.rng = random.Random(config.semilla)
        self.numero = 0
        self.historial = []
        self.mejor_historico = None
        a, b = self.problema.dominio
        self.poblacion = [
            tuple(
                self.rng.randrange(2) for _ in range(config.bits() * config.dimensiones)
            )
            if config.representacion == "Binaria"
            else tuple(self.rng.uniform(a, b) for _ in range(config.dimensiones))
            for _ in range(config.poblacion)
        ]
        self.registrar({"cruces": 0, "mutaciones": 0, "elites": 0})

    def decodificar(self, genes):
        c = self.config
        a, b = self.problema.dominio
        if c.representacion == "Real":
            return tuple(genes)
        bits = c.bits()
        vector = []
        for ini in range(0, len(genes), bits):
            entero = 0
            for bit in genes[ini : ini + bits]:
                entero = (entero << 1) | bit
            vector.append(a + entero * (b - a) / (2**bits - 1))
        return tuple(vector)

    def registrar(self, operaciones):
        valores = [self.problema.evaluar(self.decodificar(g)) for g in self.poblacion]
        orden = sorted(
            range(len(valores)),
            key=lambda i: -valores[i] if self.problema.maximizar else valores[i],
        )
        mejor = orden[0]
        if self.mejor_historico is None or (
            (valores[mejor] > self.mejor_historico)
            if self.problema.maximizar
            else (valores[mejor] < self.mejor_historico)
        ):
            self.mejor_historico = valores[mejor]
        if self.config.representacion == "Binaria":
            frecuencias = [
                fmean(g[j] for g in self.poblacion)
                for j in range(len(self.poblacion[0]))
            ]
            diversidad = fmean(2 * p * (1 - p) for p in frecuencias)
        else:
            a, b = self.problema.dominio
            diversidad = fmean(
                pstdev(g[j] for g in self.poblacion) / (b - a)
                for j in range(self.config.dimensiones)
            )
        self.valores = valores
        self.orden = orden
        snap = {
            "generacion": self.numero,
            "mejor": valores[mejor],
            "promedio": fmean(valores),
            "historico": self.mejor_historico,
            "diversidad": diversidad,
            "genes": self.poblacion[mejor],
            "vector": self.decodificar(self.poblacion[mejor]),
            "poblacion": tuple(self.poblacion),
            "objetivos": tuple(valores),
            "operaciones": operaciones,
        }
        self.historial.append(snap)
        return snap

    @property
    def terminado(self):
        return self.numero >= self.config.generaciones

    def cruzar(self, p, q):
        c = self.config
        rng = self.rng
        a, b = self.problema.dominio
        if c.representacion == "Binaria" or c.cruce == "Monopunto":
            if len(p) < 2:
                return p, q
            k = rng.randrange(1, len(p))
            return p[:k] + q[k:], q[:k] + p[k:]
        if c.cruce == "Uniforme":
            mascara = [rng.random() < 0.5 for _ in p]
            return tuple(p[i] if mascara[i] else q[i] for i in range(len(p))), tuple(
                q[i] if mascara[i] else p[i] for i in range(len(p))
            )
        if c.cruce == "Aritmético":
            return tuple(c.alfa * x + (1 - c.alfa) * y for x, y in zip(p, q)), tuple(
                (1 - c.alfa) * x + c.alfa * y for x, y in zip(p, q)
            )
        hijos = [[], []]
        for x, y in zip(p, q):
            u = rng.random()
            beta = (
                (2 * u) ** (1 / (c.eta + 1))
                if u <= 0.5
                else (1 / (2 * (1 - u))) ** (1 / (c.eta + 1))
            )
            hijos[0].append(min(b, max(a, 0.5 * ((1 + beta) * x + (1 - beta) * y))))
            hijos[1].append(min(b, max(a, 0.5 * ((1 - beta) * x + (1 + beta) * y))))
        return tuple(hijos[0]), tuple(hijos[1])

    def paso(self):
        if self.terminado:
            return self.historial[-1]
        c = self.config
        rng = self.rng
        a, b = self.problema.dominio
        nueva = [self.poblacion[i] for i in self.orden[: c.elites]]
        candidatos = seleccionar(
            self.valores,
            2 * math.ceil((c.poblacion - c.elites) / 2),
            rng,
            c.seleccion,
            self.problema.maximizar,
        )
        cruces = mutaciones = 0
        for j in range(0, len(candidatos), 2):
            p, q = (self.poblacion[candidatos[j]], self.poblacion[candidatos[j + 1]])
            if rng.random() < c.prob_cruce:
                p, q = self.cruzar(p, q)
                cruces += 1
            for hijo in (p, q):
                if len(nueva) >= c.poblacion:
                    break
                genes = list(hijo)
                for k in range(len(genes)):
                    if rng.random() < c.prob_mutacion:
                        genes[k] = (
                            1 - genes[k]
                            if c.representacion == "Binaria"
                            else rng.uniform(a, b)
                        )
                        mutaciones += 1
                nueva.append(tuple(genes))
        self.poblacion = nueva
        self.numero += 1
        return self.registrar(
            {"cruces": cruces, "mutaciones": mutaciones, "elites": c.elites}
        )

    def ejecutar(self):
        while not self.terminado:
            self.paso()
        return self.historial[-1]
