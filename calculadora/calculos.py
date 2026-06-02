import math

from calculadora.documents import ParametrosFinancieros


def obtener_parametros() -> dict:
    p = ParametrosFinancieros.obtener_vigentes()
    return {
        "insumos": p.precios_insumos,
        "reaccion": p.costos_reaccion,
        "produccion": p.valor_produccion,
    }


def calcular_perdida_proyectada(dias: int, vacas_afectadas: int) -> dict:
    """
    Estima la perdida economica si no se atiende la alerta.
    Perdida = vacas * dias * produccion_diaria * precio_litro
    """
    params = obtener_parametros()
    prod = params["produccion"]

    litros_dia = prod.get("produccion_promedio_vaca_dia", 25.0)
    precio_litro = prod.get("precio_venta_litro_leche", 11.50)

    perdida_leche = vacas_afectadas * dias * litros_dia * precio_litro
    litros_descartados = vacas_afectadas * dias * litros_dia

    return {
        "dias": dias,
        "vacas_afectadas": vacas_afectadas,
        "litros_descartados": round(litros_descartados, 2),
        "perdida_leche": round(perdida_leche, 2),
    }


def calcular_costo_prevencion(vacas_total: int, dias: int = 30) -> dict:
    """
    Costo de prevencion para el periodo indicado.
    Ordenos = dias * 2 (dos ordenos diarios).
    Pruebas CMT proporcionales al periodo (2 pruebas/vaca/mes).
    """
    params = obtener_parametros()
    insumos = params["insumos"]

    ordenos = dias * 2
    costo_sellador = insumos.get("sellador_yodo_litro", 120.50) * (vacas_total * ordenos * 0.005)
    costo_toallas = insumos.get("toallas_paquete", 85.00) * (vacas_total * ordenos / 100)
    costo_cmt = insumos.get("prueba_cmt", 45.00) * vacas_total * 2 * (dias / 30)

    total = costo_sellador + costo_toallas + costo_cmt

    return {
        "dias": dias,
        "ordenos": ordenos,
        "costo_sellador": round(costo_sellador, 2),
        "costo_toallas": round(costo_toallas, 2),
        "costo_cmt": round(costo_cmt, 2),
        "total_prevencion": round(total, 2),
    }


def calcular_costo_reaccion(vacas_enfermas: int, dias: int = 7) -> dict:
    """
    Costo de reaccionar ante mastitis: tratamiento + veterinario + leche perdida + reemplazo.
    """
    params = obtener_parametros()
    reaccion = params["reaccion"]
    prod = params["produccion"]

    litros_dia = prod.get("produccion_promedio_vaca_dia", 25.0)
    precio_litro = prod.get("precio_venta_litro_leche", 11.50)

    costo_antibiotico = reaccion.get("precio_promedio_antibiotico", 850.00) * vacas_enfermas
    costo_veterinario = reaccion.get("costo_promedio_consulta_vet", 600.00) * vacas_enfermas
    leche_perdida = vacas_enfermas * dias * litros_dia * precio_litro
    tasa_descarte = 0.15
    costo_reemplazo = reaccion.get("costo_reemplazo_vaca", 35000.00) * vacas_enfermas * tasa_descarte

    total = costo_antibiotico + costo_veterinario + leche_perdida + costo_reemplazo

    return {
        "dias": dias,
        "costo_antibiotico": round(costo_antibiotico, 2),
        "costo_veterinario": round(costo_veterinario, 2),
        "leche_perdida": round(leche_perdida, 2),
        "costo_reemplazo": round(costo_reemplazo, 2),
        "total_reaccion": round(total, 2),
    }


def calcular_roi(vacas_total: int, vacas_enfermas: int, dias: int = 30, efectividad: float = 0.7) -> dict:
    """
    ROI = (costo_sin_prevencion - costo_con_prevencion) / costo_con_prevencion * 100

    La prevencion no elimina todos los casos: con una efectividad del 70%,
    el 30% de los casos aun ocurren. El ROI compara el costo total de
    prevenir vs no hacer nada.
    """
    prevencion = calcular_costo_prevencion(vacas_total, dias)
    dias_tratamiento = min(dias, 7)
    reaccion = calcular_costo_reaccion(vacas_enfermas, dias_tratamiento)

    costo_prev = prevencion["total_prevencion"]
    costo_evitable = (
        reaccion["costo_antibiotico"]
        + reaccion["costo_veterinario"]
        + reaccion["leche_perdida"]
    )

    costo_sin_prevencion = costo_evitable
    costo_residual = costo_evitable * (1 - efectividad)
    costo_con_prevencion = costo_prev + costo_residual

    ahorro = costo_sin_prevencion - costo_con_prevencion
    roi = (ahorro / costo_con_prevencion * 100) if costo_con_prevencion > 0 else 0

    return {
        "prevencion": prevencion,
        "reaccion": reaccion,
        "ahorro_estimado": round(ahorro, 2),
        "riesgo_reemplazo": round(reaccion["costo_reemplazo"], 2),
        "roi_porcentaje": round(roi, 2),
        "efectividad": efectividad,
    }


def proyectar_contagios(vacas_infectadas_iniciales: int, dias: int, tasa_contagio: float = 0.1, vacas_total: int = 500, tasa_recuperacion: float = 0.14) -> list:
    proyeccion = []
    N = float(vacas_total)
    S = N - float(vacas_infectadas_iniciales)
    I = float(vacas_infectadas_iniciales)
    R = 0.0

    for dia in range(dias + 1):
        proyeccion.append({
            "dia": dia,
            "susceptibles": round(S),
            "infectadas": round(I),
            "recuperadas": round(R),
        })
        nuevas_infecciones = tasa_contagio * S * I / N
        nuevas_recuperaciones = tasa_recuperacion * I
        S = S - nuevas_infecciones
        I = I + nuevas_infecciones - nuevas_recuperaciones
        R = R + nuevas_recuperaciones
        if S < 0:
            S = 0.0
        if I < 0:
            I = 0.0

    return proyeccion
