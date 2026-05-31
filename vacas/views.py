from collections import OrderedDict
from datetime import datetime
from math import ceil

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect, render

from bitacora.documents import SensorLeche
from vacas.documents import Vaca, VisitaVeterinaria

POR_PAGINA = 25


def _puede_gestionar(user):
    return user.is_superuser or user.groups.filter(name="administrador").exists()


@login_required
def lista_vacas(request):
    lote = request.GET.get("lote", "")
    estado = request.GET.get("estado", "")
    vista = request.GET.get("vista", "tarjetas")
    pagina = int(request.GET.get("pagina", 1))

    mostrar_inactivas = request.GET.get("inactivas") == "1"

    qs = Vaca.objects
    if not mostrar_inactivas:
        qs = qs.filter(activa=True)
    if lote:
        qs = qs.filter(lote=lote)
    if estado:
        qs = qs.filter(estado_salud=estado)

    total = qs.count()
    total_paginas = max(ceil(total / POR_PAGINA), 1)
    pagina = max(1, min(pagina, total_paginas))
    vacas = qs.skip((pagina - 1) * POR_PAGINA).limit(POR_PAGINA)

    vacas_por_lote = OrderedDict()
    if vista == "tarjetas":
        for v in vacas:
            key = v.lote or "Sin lote"
            vacas_por_lote.setdefault(key, []).append(v)

    lotes = Vaca.objects.distinct("lote")

    return render(request, "vacas/lista.html", {
        "vacas": vacas if vista == "lista" else [],
        "vacas_por_lote": vacas_por_lote,
        "lotes": lotes,
        "filtro_lote": lote,
        "filtro_estado": estado,
        "vista": vista,
        "pagina": pagina,
        "total_paginas": total_paginas,
        "total_vacas": total,
        "mostrar_inactivas": mostrar_inactivas,
        "page_range": range(1, total_paginas + 1),
    })


@login_required
def detalle_vaca(request, vaca_id):
    vaca = Vaca.objects.get(id=vaca_id)
    visitas = VisitaVeterinaria.objects(vaca=vaca)
    ultimo_sensor = SensorLeche.objects(vaca=vaca).order_by("-fecha_medicion").first()
    return render(request, "vacas/detalle.html", {
        "vaca": vaca,
        "visitas": visitas,
        "ultimo_sensor": ultimo_sensor,
    })


@login_required
def crear_vaca(request):
    if not _puede_gestionar(request.user):
        return HttpResponseForbidden("No tienes permisos para registrar vacas.")

    if request.method == "POST":
        fecha_nac = request.POST.get("fecha_nacimiento")
        vaca = Vaca(
            arete=request.POST["arete"],
            nombre=request.POST["nombre"],
            fecha_nacimiento=datetime.strptime(fecha_nac, "%Y-%m-%d") if fecha_nac else None,
            lote=request.POST.get("lote", ""),
            estado_salud=request.POST.get("estado_salud", "Sano"),
        )
        vaca.save()
        return redirect("vacas:lista")
    return render(request, "vacas/form_vaca.html")


@login_required
def editar_vaca(request, vaca_id):
    if not _puede_gestionar(request.user):
        return HttpResponseForbidden("No tienes permisos para editar vacas.")

    vaca = Vaca.objects.get(id=vaca_id)

    if request.method == "POST":
        vaca.arete = request.POST["arete"]
        vaca.nombre = request.POST["nombre"]
        fecha_nac = request.POST.get("fecha_nacimiento")
        vaca.fecha_nacimiento = datetime.strptime(fecha_nac, "%Y-%m-%d") if fecha_nac else vaca.fecha_nacimiento
        vaca.lote = request.POST.get("lote", "")
        vaca.estado_salud = request.POST.get("estado_salud", vaca.estado_salud)

        fecha_aisl = request.POST.get("fecha_aislamiento")
        if fecha_aisl:
            vaca.fecha_aislamiento = datetime.strptime(fecha_aisl, "%Y-%m-%d")
        elif vaca.estado_salud not in ("Aislado", "Tratamiento", "Enferma"):
            vaca.fecha_aislamiento = None

        vaca.activa = request.POST.get("activa") == "on"
        if vaca.activa:
            vaca.razon_baja = ""
        else:
            vaca.razon_baja = request.POST.get("razon_baja", "")

        vaca.save()
        return redirect("vacas:detalle", vaca_id=str(vaca.id))

    return render(request, "vacas/form_vaca.html", {"vaca": vaca, "editando": True})


@login_required
def crear_visita(request, vaca_id):
    if not _puede_gestionar(request.user):
        return HttpResponseForbidden("No tienes permisos para registrar visitas.")

    vaca = Vaca.objects.get(id=vaca_id)
    if request.method == "POST":
        visita = VisitaVeterinaria(
            vaca=vaca,
            fecha_visita=datetime.strptime(request.POST["fecha_visita"], "%Y-%m-%d"),
            tipo_consulta=request.POST.get("tipo_consulta", "Rutinaria"),
            aplica_tratamiento=request.POST.get("aplica_tratamiento") == "on",
            tratamiento=request.POST.get("tratamiento", ""),
            observaciones=request.POST.get("observaciones", ""),
        )
        costo = request.POST.get("costo_total")
        if costo:
            visita.set_costo(float(costo))
        visita.save()
        return redirect("vacas:detalle", vaca_id=str(vaca.id))
    return render(request, "vacas/form_visita.html", {"vaca": vaca})


@login_required
def api_vacas_lote(request):
    lote = request.GET.get("lote", "")
    vacas = Vaca.objects
    if lote:
        vacas = vacas.filter(lote=lote)
    data = [
        {
            "id": str(v.id),
            "arete": v.arete,
            "nombre": v.nombre,
            "estado_salud": v.estado_salud,
            "lote": v.lote,
        }
        for v in vacas
    ]
    return JsonResponse(data, safe=False)
