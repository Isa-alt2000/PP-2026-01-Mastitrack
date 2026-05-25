import numpy as np


def sigmoide(x):
    return 1.0 / (1.0 + np.exp(-x))


def clasificar_nivel(probabilidad: float) -> str:
    if probabilidad < 0.3:
        return "verde"
    if probabilidad < 0.7:
        return "amarillo"
    return "rojo"


def predecir_riesgo(
    conteo_celulas_somaticas: int,
    conductividad_electrica: float,
    ph: float,
    temperatura: float,
    porcentaje_cumplimiento: float,
    fallas_criticas: int,
) -> dict:
    """
    Simula la inferencia de una red neuronal ya entrenada.
    En produccion, se cargaria el modelo real (pesos .npy o similar).
    Aqui se usan pesos ficticios para demostrar el flujo.
    """
    x = np.array([
        conteo_celulas_somaticas / 1_000_000,
        conductividad_electrica / 10.0,
        (ph - 6.0) / 1.0,
        (temperatura - 37.0) / 3.0,
        (100 - porcentaje_cumplimiento) / 100.0,
        fallas_criticas / 5.0,
    ])

    # Pesos ficticios de una red de una capa oculta (6 -> 4 -> 1)
    w1 = np.array([
        [0.8, 0.3, 0.5, 0.2, 0.6, 0.4],
        [0.2, 0.7, 0.3, 0.5, 0.4, 0.6],
        [0.5, 0.4, 0.8, 0.3, 0.7, 0.2],
        [0.3, 0.6, 0.2, 0.7, 0.5, 0.8],
    ])
    b1 = np.array([-0.5, -0.3, -0.4, -0.6])

    w2 = np.array([[0.7, 0.5, 0.6, 0.8]])
    b2 = np.array([-1.0])

    h = sigmoide(w1 @ x + b1)
    salida = sigmoide(w2 @ h + b2)
    probabilidad = float(salida[0])

    return {
        "probabilidad": round(probabilidad, 4),
        "nivel_alerta": clasificar_nivel(probabilidad),
    }
