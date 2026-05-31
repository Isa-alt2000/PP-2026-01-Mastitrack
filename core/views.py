from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from semaforo.documents import RiesgoMastitisHistorico
from vacas.documents import Vaca


@login_required
def dashboard(request):
    total_vacas = Vaca.objects(activa=True).count()
    vacas_aisladas = Vaca.objects(activa=True, estado_salud="Aislado").count()
    vacas_tratamiento = Vaca.objects(activa=True, estado_salud="Tratamiento").count()

    ultimos_riesgos = RiesgoMastitisHistorico.objects.order_by(
        "-fecha_evaluacion"
    )[:5]
    alertas_rojas = RiesgoMastitisHistorico.objects(nivel_alerta="rojo").count()

    vacas_confirmadas = Vaca.objects(activa=True, diagnostico_mastitis="confirmado")
    vacas_sospecha = Vaca.objects(activa=True, diagnostico_mastitis="sospecha_calculada")

    return render(request, "dashboard.html", {
        "total_vacas": total_vacas,
        "vacas_aisladas": vacas_aisladas,
        "vacas_tratamiento": vacas_tratamiento,
        "ultimos_riesgos": ultimos_riesgos,
        "alertas_rojas": alertas_rojas,
        "vacas_confirmadas": vacas_confirmadas,
        "vacas_sospecha": vacas_sospecha,
    })
