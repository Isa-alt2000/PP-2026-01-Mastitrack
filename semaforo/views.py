from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import render

from bitacora.documents import BitacoraOrdeno, SensorLeche
from semaforo.documents import EventoRiesgoOperativo, RiesgoMastitisHistorico
from semaforo.inference import VERSION_MODELO, predecir_riesgo
from vacas.documents import Vaca


def _puede_gestionar(user):
    return user.is_superuser or user.groups.filter(name="administrador").exists()


def _hay_datos_nuevos(vaca, ultimo_riesgo):
    ultimo_sensor = SensorLeche.objects(vaca=vaca).order_by("-fecha_medicion").first()
    if not ultimo_sensor:
        return False, ultimo_sensor
    if not ultimo_riesgo:
        return True, ultimo_sensor
    sensor_nuevo = ultimo_sensor.fecha_medicion > ultimo_riesgo.fecha_evaluacion
    modelo_nuevo = ultimo_riesgo.version_modelo != VERSION_MODELO
    return sensor_nuevo or modelo_nuevo, ultimo_sensor


def _ejecutar_evaluacion(vaca, user_id):
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
        version_modelo=VERSION_MODELO,
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

    return registro


@login_required
def panel_semaforo(request):
    if not _puede_gestionar(request.user):
        return HttpResponseForbidden("No tienes permisos para acceder al semaforo.")

    vacas = Vaca.objects.all()
    datos_vacas = []
    evaluaciones_auto = 0

    for vaca in vacas:
        ultimo_riesgo = RiesgoMastitisHistorico.objects(vaca=vaca).first()
        tiene_datos_nuevos, ultimo_sensor = _hay_datos_nuevos(vaca, ultimo_riesgo)

        if tiene_datos_nuevos and ultimo_sensor:
            ultimo_riesgo = _ejecutar_evaluacion(vaca, request.user.id)
            tiene_datos_nuevos = False
            evaluaciones_auto += 1

        datos_vacas.append({
            "vaca": vaca,
            "riesgo": ultimo_riesgo,
            "tiene_sensor": ultimo_sensor is not None,
            "puede_evaluar": tiene_datos_nuevos,
        })

    return render(request, "semaforo/panel.html", {
        "datos_vacas": datos_vacas,
        "evaluaciones_auto": evaluaciones_auto,
    })


@login_required
def evaluar_riesgo(request, vaca_id):
    if not _puede_gestionar(request.user):
        return HttpResponseForbidden("No tienes permisos para evaluar riesgo.")

    vaca = Vaca.objects.get(id=vaca_id)
    ultimo_riesgo = RiesgoMastitisHistorico.objects(vaca=vaca).first()
    tiene_datos_nuevos, ultimo_sensor = _hay_datos_nuevos(vaca, ultimo_riesgo)

    if not ultimo_sensor:
        return JsonResponse(
            {"error": "No hay datos de sensores para esta vaca."}, status=400
        )

    if not tiene_datos_nuevos:
        return JsonResponse({
            "error": "Ya se evaluo con los datos actuales. Se requieren nuevos datos de sensor o una version de modelo actualizada.",
            "ya_evaluado": True,
        }, status=409)

    registro = _ejecutar_evaluacion(vaca, request.user.id)

    return JsonResponse({
        "vaca": vaca.arete,
        "probabilidad": registro.probabilidad_riesgo,
        "nivel_alerta": registro.nivel_alerta,
        "fecha": registro.fecha_evaluacion.strftime("%d/%m/%Y %H:%M"),
    })


@login_required
def historial_riesgo(request, vaca_id):
    if not _puede_gestionar(request.user):
        return HttpResponseForbidden("No tienes permisos para ver el historial de riesgo.")
    vaca = Vaca.objects.get(id=vaca_id)
    registros = RiesgoMastitisHistorico.objects(vaca=vaca)[:20]
    return render(request, "semaforo/historial.html", {
        "vaca": vaca,
        "registros": registros,
    })
