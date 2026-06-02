import random
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from core.crypto import descifrar
from semaforo.documents import RiesgoMastitisHistorico
from vacas.documents import Vaca

SALUDOS_FIJOS = [
    "Bienvenido de vuelta",
    "Listo para trabajar",
    "El hato te espera",
    "Todo bajo control",
    "Manos a la obra",
    "Un dia productivo te espera",
    "A cuidar el ganado",
]


def _saludo_por_hora():
    hora = datetime.now().hour
    if 5 <= hora < 12:
        return "Buenos dias"
    if 12 <= hora < 19:
        return "Buenas tardes"
    return "Buenas noches"


def _mensaje_bienvenida():
    opciones = SALUDOS_FIJOS + [None, None, None]
    elegido = random.choice(opciones)
    return elegido if elegido else _saludo_por_hora()


@login_required
def dashboard(request):
    total_vacas = Vaca.objects(activa=True).count()
    vacas_aisladas = Vaca.objects(activa=True, estado_salud="Aislado").count()
    vacas_tratamiento = Vaca.objects(activa=True, estado_salud="Tratamiento").count()

    ultimos_riesgos = RiesgoMastitisHistorico.objects.order_by(
        "-fecha_evaluacion"
    )[:5]
    ultimas_por_vaca = RiesgoMastitisHistorico.objects.aggregate([
        {"$sort": {"fecha_evaluacion": -1}},
        {"$group": {
            "_id": "$vaca",
            "nivel_alerta_cifrado": {"$first": "$nivel_alerta_cifrado"},
        }},
    ])
    alertas_rojas = sum(
        1 for r in ultimas_por_vaca
        if r.get("nivel_alerta_cifrado")
        and descifrar(r["nivel_alerta_cifrado"]) == "rojo"
    )

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
        "mensaje_bienvenida": _mensaje_bienvenida(),
    })


@login_required
def acerca(request):
    return render(request, "acerca.html")
