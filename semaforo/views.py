from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import render

from bitacora.documents import SensorLeche
from semaforo.documents import RiesgoMastitisHistorico
from semaforo.services import evaluar_vaca, hay_datos_nuevos
from vacas.documents import Vaca


def _puede_gestionar(user):
    return user.is_superuser or user.groups.filter(name="administrador").exists()


@login_required
def panel_semaforo(request):
    if not _puede_gestionar(request.user):
        return HttpResponseForbidden("No tienes permisos para acceder al semaforo.")

    vacas = Vaca.objects.all()
    datos_vacas = []
    evaluaciones_auto = 0

    for vaca in vacas:
        necesita, ultimo_sensor = hay_datos_nuevos(vaca)

        if necesita and ultimo_sensor:
            ultimo_riesgo = evaluar_vaca(vaca, request.user.id)
            necesita = False
            evaluaciones_auto += 1
        else:
            ultimo_riesgo = RiesgoMastitisHistorico.objects(vaca=vaca).first()

        datos_vacas.append({
            "vaca": vaca,
            "riesgo": ultimo_riesgo,
            "tiene_sensor": ultimo_sensor is not None,
            "puede_evaluar": necesita,
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
    necesita, ultimo_sensor = hay_datos_nuevos(vaca)

    if not ultimo_sensor:
        return JsonResponse(
            {"error": "No hay datos de sensores para esta vaca."}, status=400
        )

    if not necesita:
        return JsonResponse({
            "error": "Ya se evaluo con los datos actuales. Se requieren nuevos datos de sensor o una version de modelo actualizada.",
            "ya_evaluado": True,
        }, status=409)

    registro = evaluar_vaca(vaca, request.user.id)

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
