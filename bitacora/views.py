from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render

from bitacora.documents import BitacoraOrdeno, SensorLeche
from vacas.documents import Vaca


@login_required
def lista_bitacoras(request):
    lote = request.GET.get("lote", "")
    bitacoras = BitacoraOrdeno.objects
    if lote:
        bitacoras = bitacoras.filter(lote=lote)
    bitacoras = bitacoras[:50]
    return render(request, "bitacora/lista.html", {"bitacoras": bitacoras})


@login_required
def crear_bitacora(request):
    if request.method == "POST":
        vaca_id = request.POST.get("vaca_id", "").strip()
        if not vaca_id:
            vacas = Vaca.objects.all()
            return render(request, "bitacora/form_bitacora.html", {
                "vacas": vacas,
                "error": "Debes seleccionar una vaca.",
            })
        vaca = Vaca.objects.get(id=vaca_id)

        ordeno = {
            "pre_ordeno": {
                "lavado_manos": request.POST.get("lavado_manos") == "on",
                "despunte_primeros_chorros": request.POST.get("despunte_primeros_chorros") == "on",
                "sellado_yodo": request.POST.get("sellado_yodo") == "on",
                "secado_toalla_limpia": request.POST.get("secado_toalla_limpia") == "on",
                "fecha_pre": datetime.now().isoformat(),
            },
            "medicion_ordeno": {
                "colocacion_pezoneras": request.POST.get("colocacion_pezoneras") == "on",
                "verificar_vacio": request.POST.get("verificar_vacio") == "on",
                "retirar_pezoneras": request.POST.get("retirar_pezoneras") == "on",
                "fecha_med": datetime.now().isoformat(),
            },
            "post_ordeno": {
                "sellado_post_ordeno": request.POST.get("sellado_post_ordeno") == "on",
                "limpieza_cip": request.POST.get("limpieza_cip") == "on",
                "registro_temp_tanque": request.POST.get("registro_temp_tanque") == "on",
                "firma_operador": request.POST.get("firma_operador") == "on",
                "fecha_post": datetime.now().isoformat(),
            },
        }

        bitacora = BitacoraOrdeno(
            vaca=vaca,
            fecha_ordeno=datetime.now(),
            operador_id=str(request.user.id),
            lote=vaca.lote,
            ordeno=ordeno,
        )
        bitacora.calcular_metricas()
        bitacora.save()

        return redirect("bitacora:detalle", bitacora_id=str(bitacora.id))

    vacas = Vaca.objects.all()
    return render(request, "bitacora/form_bitacora.html", {"vacas": vacas})


@login_required
def detalle_bitacora(request, bitacora_id):
    bitacora = BitacoraOrdeno.objects.get(id=bitacora_id)
    sensor = SensorLeche.objects(bitacora_ordeno=bitacora).first()
    return render(request, "bitacora/detalle.html", {
        "bitacora": bitacora,
        "sensor": sensor,
    })


@login_required
def registrar_sensor(request, bitacora_id):
    bitacora = BitacoraOrdeno.objects.get(id=bitacora_id)
    if request.method == "POST":
        sensor = SensorLeche(
            vaca=bitacora.vaca,
            bitacora_ordeno=bitacora,
            conteo_celulas_somaticas=int(request.POST.get("conteo_celulas_somaticas", 0)),
            ph=float(request.POST.get("ph", 6.8)),
            temperatura=float(request.POST.get("temperatura", 38.5)),
            conductividad_electrica=float(request.POST.get("conductividad_electrica", 5.0)),
            fecha_medicion=datetime.now(),
        )
        sensor.save()
        return redirect("bitacora:detalle", bitacora_id=str(bitacora.id))
    return render(request, "bitacora/form_sensor.html", {"bitacora": bitacora})


@login_required
def api_bitacora_resumen(request, vaca_id):
    vaca = Vaca.objects.get(id=vaca_id)
    bitacoras = BitacoraOrdeno.objects(vaca=vaca)[:10]
    data = []
    for b in bitacoras:
        metricas = b.metricas or {}
        data.append({
            "id": str(b.id),
            "fecha": b.fecha_ordeno.isoformat() if b.fecha_ordeno else None,
            "porcentaje_cumplimiento": metricas.get("porcentaje_cumplimiento", 0),
            "fallas_criticas": metricas.get("fallas_criticas", 0),
        })
    return JsonResponse(data, safe=False)
