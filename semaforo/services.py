import logging
from datetime import datetime

from bitacora.documents import BitacoraOrdeno, SensorLeche
from semaforo.documents import EventoRiesgoOperativo, RiesgoMastitisHistorico
from semaforo.inference import get_version_modelo, predecir_riesgo
from vacas.documents import Vaca

log = logging.getLogger(__name__)


def hay_datos_nuevos(vaca):
    ultimo_sensor = SensorLeche.objects(vaca=vaca).order_by("-fecha_medicion").first()
    if not ultimo_sensor:
        return False, ultimo_sensor
    ultimo_riesgo = RiesgoMastitisHistorico.objects(vaca=vaca).first()
    if not ultimo_riesgo:
        return True, ultimo_sensor
    sensor_nuevo = ultimo_sensor.fecha_medicion > ultimo_riesgo.fecha_evaluacion
    modelo_nuevo = ultimo_riesgo.version_modelo != get_version_modelo()
    return sensor_nuevo or modelo_nuevo, ultimo_sensor


def evaluar_vaca(vaca, user_id):
    ultima_bitacora = BitacoraOrdeno.objects(vaca=vaca).order_by("-fecha_ordeno").first()
    ultimo_sensor = SensorLeche.objects(vaca=vaca).order_by("-fecha_medicion").first()

    if not ultimo_sensor:
        return None

    cumplimiento = 0.0
    fallas = 0
    bitacora_ref = None
    if ultima_bitacora and ultima_bitacora.metricas:
        cumplimiento = ultima_bitacora.metricas.get("porcentaje_cumplimiento", 0)
        fallas = ultima_bitacora.metricas.get("fallas_criticas", 0)
        bitacora_ref = ultima_bitacora

    resultado = predecir_riesgo(
        conteo_celulas_somaticas=ultimo_sensor.conteo_celulas_somaticas or 0,
        conductividad_electrica=ultimo_sensor.conductividad_electrica or 0,
        ph=ultimo_sensor.ph or 6.8,
        temperatura=ultimo_sensor.temperatura or 38.5,
        porcentaje_cumplimiento=cumplimiento,
        fallas_criticas=fallas,
    )

    registro = RiesgoMastitisHistorico(
        vaca=vaca,
        bitacora_ordeno=bitacora_ref,
        sensor_leche=ultimo_sensor,
        fecha_evaluacion=datetime.now(),
        probabilidad_riesgo=resultado["probabilidad"],
        nivel_alerta=resultado["nivel_alerta"],
        version_modelo=get_version_modelo(),
    )
    registro.save()

    EventoRiesgoOperativo(
        vaca=vaca,
        bitacora_ordeno=bitacora_ref,
        sensor_leche=ultimo_sensor,
        riesgo=registro,
        fecha_evento=datetime.now(),
        operador_id=str(user_id),
        lote=vaca.lote,
        porcentaje_cumplimiento=cumplimiento,
        fallas_criticas=fallas,
        conteo_celulas_somaticas=ultimo_sensor.conteo_celulas_somaticas,
        conductividad_electrica=ultimo_sensor.conductividad_electrica,
        probabilidad_riesgo=resultado["probabilidad"],
        nivel_alerta=resultado["nivel_alerta"],
    ).save()

    if resultado["nivel_alerta"] == "rojo":
        if vaca.diagnostico_mastitis != "confirmado":
            vaca.diagnostico_mastitis = "sospecha_calculada"
            vaca.save()
            log.info(f"Sospecha calculada para {vaca.arete} (prob={resultado['probabilidad']:.4f})")
    elif vaca.diagnostico_mastitis == "sospecha_descartada":
        vaca.diagnostico_mastitis = None
        vaca.save()
        log.info(f"Sospecha descartada limpiada para {vaca.arete}")

    log.info(f"Evaluacion {vaca.arete}: {resultado['nivel_alerta']} ({resultado['probabilidad']:.4f}) modelo={get_version_modelo()}")

    return registro


def reevaluar_todas(user_id):
    vacas = Vaca.objects(activa=True)
    evaluadas = 0
    for vaca in vacas:
        necesita, sensor = hay_datos_nuevos(vaca)
        if necesita and sensor:
            evaluar_vaca(vaca, user_id)
            evaluadas += 1
    log.info(f"Re-evaluacion masiva: {evaluadas} vacas actualizadas")
    return evaluadas
