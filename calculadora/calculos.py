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


def calcular_roi(vacas_total: int, vacas_enfermas: int, dias: int = 30) -> dict:
    """
    ROI = (costo_reaccion - costo_prevencion) / costo_prevencion * 100
    """
    prevencion = calcular_costo_prevencion(vacas_total, dias)
    reaccion = calcular_costo_reaccion(vacas_enfermas, dias)

    costo_prev = prevencion["total_prevencion"]
    costo_reac = reaccion["total_reaccion"]

    ahorro = costo_reac - costo_prev
    roi = (ahorro / costo_prev * 100) if costo_prev > 0 else 0

    return {
        "prevencion": prevencion,
        "reaccion": reaccion,
        "ahorro_estimado": round(ahorro, 2),
        "roi_porcentaje": round(roi, 2),
    }


def proyectar_contagios(vacas_infectadas_iniciales: int, dias: int, tasa_contagio: float = 0.1, vacas_total: int = 500) -> list:
    proyeccion = []
    infectadas = float(vacas_infectadas_iniciales)

    for dia in range(dias + 1):
        proyeccion.append({
            "dia": dia,
            "infectadas": round(infectadas),
        })
        nuevas = infectadas * tasa_contagio
        infectadas = infectadas + nuevas
        if infectadas > vacas_total:
            infectadas = vacas_total

    return proyeccion
