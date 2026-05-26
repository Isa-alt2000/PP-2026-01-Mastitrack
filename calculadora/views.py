from datetime import datetime

from functools import wraps

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST


def requiere_gestion(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not (request.user.is_superuser or request.user.groups.filter(name="administrador").exists()):
            return HttpResponseForbidden("No tienes permisos para acceder a esta seccion.")
        return view_func(request, *args, **kwargs)
    return wrapper

from calculadora.calculos import (
    calcular_costo_prevencion,
    calcular_costo_reaccion,
    calcular_perdida_proyectada,
    calcular_roi,
    proyectar_contagios,
)
from calculadora.documents import ParametrosFinancieros


@login_required
@requiere_gestion
def panel_calculadora(request):
    params = ParametrosFinancieros.obtener_vigentes()
    return render(request, "calculadora/panel.html", {"params": params})


@login_required
@requiere_gestion
@require_GET
def api_perdida_proyectada(request):
    dias = int(request.GET.get("dias", 7))
    vacas = int(request.GET.get("vacas", 1))
    resultado = calcular_perdida_proyectada(dias, vacas)
    return JsonResponse(resultado)


@login_required
@requiere_gestion
@require_GET
def api_roi(request):
    vacas_total = int(request.GET.get("vacas_total", 50))
    vacas_enfermas = int(request.GET.get("vacas_enfermas", 5))
    resultado = calcular_roi(vacas_total, vacas_enfermas)
    return JsonResponse(resultado)


@login_required
@requiere_gestion
@require_GET
def api_proyeccion_contagios(request):
    infectadas = int(request.GET.get("infectadas", 2))
    dias = int(request.GET.get("dias", 14))
    tasa = float(request.GET.get("tasa", 0.1))
    resultado = proyectar_contagios(infectadas, dias, tasa)
    return JsonResponse({"proyeccion": resultado})


@login_required
@requiere_gestion
@require_GET
def api_prevencion_vs_reaccion(request):
    vacas_total = int(request.GET.get("vacas_total", 50))
    vacas_enfermas = int(request.GET.get("vacas_enfermas", 5))
    prevencion = calcular_costo_prevencion(vacas_total)
    reaccion = calcular_costo_reaccion(vacas_enfermas)
    return JsonResponse({
        "prevencion": prevencion,
        "reaccion": reaccion,
    })


@login_required
@requiere_gestion
def admin_parametros(request):
    params = ParametrosFinancieros.obtener_vigentes()
    if request.method == "POST":
        params.precios_insumos = {
            "sellador_yodo_litro": float(request.POST.get("sellador_yodo_litro", 120.50)),
            "toallas_paquete": float(request.POST.get("toallas_paquete", 85.00)),
            "prueba_cmt": float(request.POST.get("prueba_cmt", 45.00)),
        }
        params.costos_reaccion = {
            "precio_promedio_antibiotico": float(request.POST.get("precio_promedio_antibiotico", 850.00)),
            "costo_promedio_consulta_vet": float(request.POST.get("costo_promedio_consulta_vet", 600.00)),
            "costo_reemplazo_vaca": float(request.POST.get("costo_reemplazo_vaca", 35000.00)),
        }
        params.valor_produccion = {
            "precio_venta_litro_leche": float(request.POST.get("precio_venta_litro_leche", 11.50)),
            "produccion_promedio_vaca_dia": float(request.POST.get("produccion_promedio_vaca_dia", 25.0)),
        }
        params.fecha_actualizacion = datetime.now()
        params.save()
        return render(request, "calculadora/admin_parametros.html", {
            "params": params,
            "guardado": True,
        })
    return render(request, "calculadora/admin_parametros.html", {"params": params})
