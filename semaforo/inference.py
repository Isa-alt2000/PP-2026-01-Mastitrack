import logging

import numpy as np

log = logging.getLogger(__name__)

_VERSION_BASE = "rn_v1_base"

_modelo_joblib = None
_version_actual = _VERSION_BASE
_inicializado = False


def _sigmoide(x):
    return 1.0 / (1.0 + np.exp(-x))


def clasificar_nivel(probabilidad: float) -> str:
    if probabilidad < 0.3:
        return "verde"
    if probabilidad < 0.7:
        return "amarillo"
    return "rojo"


def recargar_modelo():
    global _modelo_joblib, _version_actual, _inicializado
    _inicializado = True

    try:
        from django.conf import settings
        from entrenamiento.documents import ModeloEntrenado

        activo = ModeloEntrenado.objects(activo=True).first()
        if activo:
            ruta = settings.MODELOS_DIR / activo.archivo
            if not ruta.exists():
                log.error(f"Modelo activo '{activo.nombre}' no encontrado en disco: {ruta}")
            else:
                import joblib

                _modelo_joblib = joblib.load(ruta)
                _version_actual = activo.nombre
                log.info(f"Modelo cargado: {activo.nombre} ({ruta.name})")
                return
    except Exception as e:
        log.error(f"Error al cargar modelo entrenado: {e}")

    _modelo_joblib = None
    _version_actual = _VERSION_BASE


def validar_modelo(ruta):
    import joblib

    modelo = joblib.load(ruta)
    if not hasattr(modelo, "predict_proba"):
        raise ValueError("El modelo no tiene metodo predict_proba.")
    import numpy as np

    x_prueba = np.zeros((1, 6))
    modelo.predict_proba(x_prueba)
    return modelo


def _asegurar_inicializado():
    if not _inicializado:
        recargar_modelo()


def get_version_modelo():
    _asegurar_inicializado()
    return _version_actual


def predecir_riesgo(
    conteo_celulas_somaticas: int,
    conductividad_electrica: float,
    ph: float,
    temperatura: float,
    porcentaje_cumplimiento: float,
    fallas_criticas: int,
) -> dict:
    _asegurar_inicializado()

    x = np.array([
        conteo_celulas_somaticas / 1_000_000,
        conductividad_electrica / 10.0,
        (ph - 6.0) / 1.0,
        (temperatura - 37.0) / 3.0,
        (100 - porcentaje_cumplimiento) / 100.0,
        fallas_criticas / 5.0,
    ])

    prob_base = _inferencia_base(x)

    if _modelo_joblib is not None:
        try:
            prob_modelo = float(
                _modelo_joblib.predict_proba(x.reshape(1, -1))[0][1]
            )
            probabilidad = prob_base * 0.6 + prob_modelo * 0.4
        except Exception:
            probabilidad = prob_base
    else:
        probabilidad = prob_base

    return {
        "probabilidad": round(probabilidad, 4),
        "nivel_alerta": clasificar_nivel(probabilidad),
    }


def _inferencia_base(x):
    w1 = np.array([
        [5.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 3.0, 2.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 5.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 3.0, 4.0],
    ])
    b1 = np.array([-2.0, -3.5, -1.5, -1.5])
    w2 = np.array([[2.5, 1.5, 1.0, 0.8]])
    b2 = np.array([-3.0])

    h = _sigmoide(w1 @ x + b1)
    salida = _sigmoide(w2 @ h + b2)
    return float(salida[0])
