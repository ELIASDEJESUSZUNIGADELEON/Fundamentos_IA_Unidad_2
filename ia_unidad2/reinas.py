"""N reinas con cromosomas que son permutaciones; sin soluciones precargadas."""

from dataclasses import dataclass
import random
from statistics import fmean


def ataques(genes):
    if sorted(genes) != list(range(len(genes))):
        raise ValueError("El cromosoma debe ser una permutación de 0 a N−1.")
    return [
        (i, j)
        for i in range(len(genes))
        for j in range(i + 1, len(genes))
        if abs(genes[i] - genes[j]) == j - i
    ]


def cruce_orden(p, q, rng):
    n = len(p)
    if n < 2:
        return tuple(p)
    a, b = sorted(rng.sample(range(n + 1), 2))
    hijo = [None] * n
    hijo[a:b] = p[a:b]
    faltantes = [q[(b + i) % n] for i in range(n) if q[(b + i) % n] not in hijo]
    huecos = [(b + i) % n for i in range(n) if hijo[(b + i) % n] is None]
    for i, valor in zip(huecos, faltantes):
        hijo[i] = valor
    return tuple(hijo)


def cruce_ciclos(p, q, rng):
    n = len(p)
    hijo = [None] * n
    restantes = set(range(n))
    copiar = True
    while restantes:
        i = min(restantes)
        while i in restantes:
            hijo[i] = p[i] if copiar else q[i]
            restantes.remove(i)
            i = p.index(q[i])
        copiar = not copiar
    return tuple(hijo)


@dataclass(frozen=True)
class ConfiguracionReinas:
    n: int = 12
    poblacion: int = 100
    generaciones: int = 500
    prob_cruce: float = 0.9
    prob_mutacion: float = 0.22
    elites: int = 2
    seleccion: str = "Torneo"
    cruce: str = "Orden OX"
    semilla: int = 2430085

    def validar(self):
        if not 1 <= self.n <= 32:
            raise ValueError("N debe estar entre 1 y 32.")
        if not 4 <= self.poblacion <= 300:
            raise ValueError("Población entre 4 y 300.")
        if not 0 <= self.generaciones <= 1000:
            raise ValueError("Generaciones entre 0 y 1000.")
        if self.poblacion * (self.generaciones + 1) > 160_000:
            raise ValueError("Reduce el tamaño del historial.")
        if not 0 <= self.elites < self.poblacion:
            raise ValueError("Elitismo fuera de rango.")
        if not 0 <= self.prob_cruce <= 1 or not 0 <= self.prob_mutacion <= 1:
            raise ValueError("Probabilidades entre 0 y 1.")
        if self.seleccion not in {"Torneo", "Ruleta"} or self.cruce not in {
            "Orden OX",
            "Ciclos CX",
        }:
            raise ValueError("Operador desconocido.")


class MotorReinas:
    def __init__(self, config=ConfiguracionReinas()):
        config.validar()
        self.config = config
        self.rng = random.Random(config.semilla)
        self.poblacion = [
            tuple(self.rng.sample(range(config.n), config.n))
            for _ in range(config.poblacion)
        ]
        self.numero = 0
        self.historial = []
        self.registrar({"cruces": 0, "intercambios": 0})

    def registrar(self, operaciones):
        self.conflictos = [len(ataques(g)) for g in self.poblacion]
        self.orden = sorted(
            range(len(self.poblacion)), key=lambda i: self.conflictos[i]
        )
        idx = self.orden[0]
        s = {
            "generacion": self.numero,
            "mejor": self.conflictos[idx],
            "promedio": fmean(self.conflictos),
            "genes": self.poblacion[idx],
            "poblacion": tuple(self.poblacion),
            "conflictos": tuple(self.conflictos),
            "distintos": len(set(self.poblacion)),
            "operaciones": operaciones,
        }
        self.historial.append(s)
        return s

    @property
    def terminado(self):
        return (
            self.historial[-1]["mejor"] == 0 or self.numero >= self.config.generaciones
        )

    def padre(self):
        if self.config.seleccion == "Torneo":
            return self.poblacion[
                min(
                    self.rng.sample(range(len(self.poblacion)), 3),
                    key=lambda i: self.conflictos[i],
                )
            ]
        return self.rng.choices(
            self.poblacion, weights=[1 / (1 + c) for c in self.conflictos], k=1
        )[0]

    def paso(self):
        if self.terminado:
            return self.historial[-1]
        c = self.config
        nueva = [self.poblacion[i] for i in self.orden[: c.elites]]
        cruzador = cruce_orden if c.cruce == "Orden OX" else cruce_ciclos
        cruces = mutaciones = 0
        while len(nueva) < c.poblacion:
            p, q = self.padre(), self.padre()
            if self.rng.random() < c.prob_cruce:
                hijos = [cruzador(p, q, self.rng), cruzador(q, p, self.rng)]
                cruces += 1
            else:
                hijos = [p, q]
            for hijo in hijos:
                if len(nueva) >= c.poblacion:
                    break
                if c.n > 1 and self.rng.random() < c.prob_mutacion:
                    a, b = self.rng.sample(range(c.n), 2)
                    g = list(hijo)
                    g[a], g[b] = g[b], g[a]
                    hijo = tuple(g)
                    mutaciones += 1
                nueva.append(hijo)
        self.poblacion = nueva
        self.numero += 1
        return self.registrar({"cruces": cruces, "intercambios": mutaciones})

    def ejecutar(self):
        while not self.terminado:
            self.paso()
        return self.historial[-1]
