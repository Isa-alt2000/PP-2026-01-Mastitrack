import logging
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect, render

from bitacora.documents import BitacoraOrdeno, SensorLeche
from vacas.documents import Vaca

log = logging.getLogger(__name__)


@login_required
def lista_bitacoras(request):
    lote = request.GET.get("lote", "")
    cumplimiento = request.GET.get("cumplimiento", "")
    bitacoras = BitacoraOrdeno.objects
    if lote:
        bitacoras = bitacoras.filter(lote=lote)
    bitacoras = list(bitacoras[:50])
    if cumplimiento == "alto":
        bitacoras = [b for b in bitacoras if b.metricas and b.metricas.get("porcentaje_cumplimiento", 0) >= 80]
    elif cumplimiento == "medio":
        bitacoras = [b for b in bitacoras if b.metricas and 50 <= b.metricas.get("porcentaje_cumplimiento", 0) < 80]
    elif cumplimiento == "bajo":
        bitacoras = [b for b in bitacoras if b.metricas and b.metricas.get("porcentaje_cumplimiento", 0) < 50]
    lotes = BitacoraOrdeno.objects.distinct("lote")
    return render(request, "bitacora/lista.html", {
        "bitacoras": bitacoras,
        "lotes": lotes,
        "filtro_lote": lote,
        "filtro_cumplimiento": cumplimiento,
        "total_bitacoras": len(bitacoras),
    })


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
    from bitacora.validators import RANGOS, validar_sensor_completo

    bitacora = BitacoraOrdeno.objects.get(id=bitacora_id)
    if request.method == "POST":
        raw = {
            "conteo_celulas_somaticas": request.POST.get("conteo_celulas_somaticas"),
            "ph": request.POST.get("ph"),
            "temperatura": request.POST.get("temperatura"),
            "conductividad_electrica": request.POST.get("conductividad_electrica"),
        }
        datos, errores, banderas = validar_sensor_completo(raw)
        if errores:
            return render(request, "bitacora/form_sensor.html", {
                "bitacora": bitacora,
                "errores": errores,
                "valores": raw,
                "rangos": RANGOS,
            })

        diag = request.POST.get("diagnostico_mastitis", "")
        diag_valor = None
        if diag == "1":
            diag_valor = True
        elif diag == "0":
            diag_valor = False

        sensor = SensorLeche(
            vaca=bitacora.vaca,
            bitacora_ordeno=bitacora,
            conteo_celulas_somaticas=datos["conteo_celulas_somaticas"],
            ph=datos["ph"],
            temperatura=datos["temperatura"],
            conductividad_electrica=datos["conductividad_electrica"],
            banderas_calidad=banderas,
            diagnostico_mastitis=diag_valor,
            origen="manual",
            fecha_medicion=datetime.now(),
        )
        sensor.save()
        log.info(f"Sensor registrado para {bitacora.vaca.arete} por {request.user.username} (CCS={datos['conteo_celulas_somaticas']}, pH={datos['ph']}, T={datos['temperatura']}, C={datos['conductividad_electrica']})")

        from semaforo.services import evaluar_vaca
        evaluar_vaca(bitacora.vaca, request.user.id)

        return redirect("bitacora:detalle", bitacora_id=str(bitacora.id))
    return render(request, "bitacora/form_sensor.html", {
        "bitacora": bitacora,
        "rangos": RANGOS,
    })


@login_required
def editar_sensor(request, sensor_id):
    from bitacora.validators import RANGOS, validar_sensor_completo

    if not (request.user.is_superuser or request.user.groups.filter(name="administrador").exists()):
        return HttpResponseForbidden("No tienes permisos para editar sensores.")

    sensor = SensorLeche.objects.get(id=sensor_id)

    if request.method == "POST":
        raw = {
            "conteo_celulas_somaticas": request.POST.get("conteo_celulas_somaticas"),
            "ph": request.POST.get("ph"),
            "temperatura": request.POST.get("temperatura"),
            "conductividad_electrica": request.POST.get("conductividad_electrica"),
        }
        datos, errores, banderas = validar_sensor_completo(raw)
        if errores:
            return render(request, "bitacora/form_sensor.html", {
                "sensor": sensor,
                "editando": True,
                "errores": errores,
                "valores": raw,
                "rangos": RANGOS,
            })

        diag = request.POST.get("diagnostico_mastitis", "")
        if diag == "1":
            sensor.diagnostico_mastitis = True
        elif diag == "0":
            sensor.diagnostico_mastitis = False
        else:
            sensor.diagnostico_mastitis = None

        sensor.conteo_celulas_somaticas = datos["conteo_celulas_somaticas"]
        sensor.ph = datos["ph"]
        sensor.temperatura = datos["temperatura"]
        sensor.conductividad_electrica = datos["conductividad_electrica"]
        sensor.banderas_calidad = banderas
        sensor.fiable = True
        sensor.save()

        ultimo = SensorLeche.objects(vaca=sensor.vaca).order_by("-fecha_medicion").first()
        if ultimo and str(ultimo.id) == str(sensor.id):
            from semaforo.services import evaluar_vaca
            evaluar_vaca(sensor.vaca, request.user.id)

        return redirect("vacas:detalle", vaca_id=str(sensor.vaca.id))

    valores = {
        "conteo_celulas_somaticas": sensor.conteo_celulas_somaticas,
        "ph": sensor.ph,
        "temperatura": sensor.temperatura,
        "conductividad_electrica": sensor.conductividad_electrica,
        "diagnostico_mastitis": sensor.diagnostico_mastitis,
    }
    return render(request, "bitacora/form_sensor.html", {
        "sensor": sensor,
        "editando": True,
        "valores": valores,
        "rangos": RANGOS,
    })


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
