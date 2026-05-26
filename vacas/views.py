from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect, render

from vacas.documents import Vaca, VisitaVeterinaria


def _puede_gestionar(user):
    return user.is_superuser or user.groups.filter(name="administrador").exists()


@login_required
def lista_vacas(request):
    lote = request.GET.get("lote", "")
    estado = request.GET.get("estado", "")

    vacas = Vaca.objects
    if lote:
        vacas = vacas.filter(lote=lote)
    if estado:
        vacas = vacas.filter(estado_salud=estado)

    lotes = Vaca.objects.distinct("lote")

    return render(request, "vacas/lista.html", {
        "vacas": vacas,
        "lotes": lotes,
        "filtro_lote": lote,
        "filtro_estado": estado,
    })


@login_required
def detalle_vaca(request, vaca_id):
    vaca = Vaca.objects.get(id=vaca_id)
    visitas = VisitaVeterinaria.objects(vaca=vaca)
    return render(request, "vacas/detalle.html", {
        "vaca": vaca,
        "visitas": visitas,
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
        elif vaca.estado_salud not in ("Aislado", "Tratamiento"):
            vaca.fecha_aislamiento = None

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
