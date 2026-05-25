from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from semaforo.documents import RiesgoMastitisHistorico
from vacas.documents import Vaca


@login_required
def dashboard(request):
    total_vacas = Vaca.objects.count()
    vacas_aisladas = Vaca.objects(estado_salud="Aislado").count()
    vacas_tratamiento = Vaca.objects(estado_salud="Tratamiento").count()

    ultimos_riesgos = RiesgoMastitisHistorico.objects.order_by(
        "-fecha_evaluacion"
    )[:5]
    alertas_rojas = RiesgoMastitisHistorico.objects(nivel_alerta="rojo").count()

    return render(request, "dashboard.html", {
        "total_vacas": total_vacas,
        "vacas_aisladas": vacas_aisladas,
        "vacas_tratamiento": vacas_tratamiento,
        "ultimos_riesgos": ultimos_riesgos,
        "alertas_rojas": alertas_rojas,
    })
