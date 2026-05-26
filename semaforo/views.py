from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import render


def _puede_gestionar(user):
    return user.is_superuser or user.groups.filter(name="administrador").exists()

from bitacora.documents import BitacoraOrdeno, SensorLeche
from semaforo.documents import EventoRiesgoOperativo, RiesgoMastitisHistorico
from semaforo.inference import predecir_riesgo
from vacas.documents import Vaca


@login_required
def panel_semaforo(request):
    if not _puede_gestionar(request.user):
        return HttpResponseForbidden("No tienes permisos para acceder al semaforo.")
    vacas = Vaca.objects.all()
    riesgos_por_vaca = {}
    for vaca in vacas:
        ultimo = RiesgoMastitisHistorico.objects(vaca=vaca).first()
        if ultimo:
            riesgos_por_vaca[str(vaca.id)] = {
                "probabilidad": ultimo.probabilidad_riesgo,
                "nivel": ultimo.nivel_alerta,
                "fecha": ultimo.fecha_evaluacion,
            }
    return render(request, "semaforo/panel.html", {
        "vacas": vacas,
        "riesgos": riesgos_por_vaca,
    })


@login_required
def evaluar_riesgo(request, vaca_id):
    if not _puede_gestionar(request.user):
        return HttpResponseForbidden("No tienes permisos para evaluar riesgo.")
    vaca = Vaca.objects.get(id=vaca_id)

    ultima_bitacora = BitacoraOrdeno.objects(vaca=vaca).order_by("-fecha_ordeno").first()
    ultimo_sensor = SensorLeche.objects(vaca=vaca).order_by("-fecha_medicion").first()

    if not ultimo_sensor:
        return JsonResponse(
            {"error": "No hay datos de sensores para esta vaca."}, status=400
        )

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
        version_modelo="rn_v1",
    )
    registro.save()

    evento = EventoRiesgoOperativo(
        vaca=vaca,
        bitacora_ordeno=bitacora_ref,
        sensor_leche=ultimo_sensor,
        riesgo=registro,
        fecha_evento=datetime.now(),
        operador_id=str(request.user.id),
        lote=vaca.lote,
        porcentaje_cumplimiento=cumplimiento,
        fallas_criticas=fallas,
        conteo_celulas_somaticas=ultimo_sensor.conteo_celulas_somaticas,
        conductividad_electrica=ultimo_sensor.conductividad_electrica,
        probabilidad_riesgo=resultado["probabilidad"],
        nivel_alerta=resultado["nivel_alerta"],
    )
    evento.save()

    return JsonResponse({
        "vaca": vaca.arete,
        "probabilidad": resultado["probabilidad"],
        "nivel_alerta": resultado["nivel_alerta"],
        "fecha": registro.fecha_evaluacion.isoformat(),
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
