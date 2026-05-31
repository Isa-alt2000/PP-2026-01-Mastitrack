import csv
import logging
from datetime import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect, render

from bitacora.documents import BitacoraOrdeno, SensorLeche
from entrenamiento.documents import ModeloEntrenado

log = logging.getLogger(__name__)


def _puede_gestionar(user):
    return user.is_superuser or user.groups.filter(name="administrador").exists()


@login_required
def panel(request):
    if not _puede_gestionar(request.user):
        return HttpResponseForbidden("No tienes permisos.")
    modelos = ModeloEntrenado.objects.all()
    activo = ModeloEntrenado.objects(activo=True).first()
    return render(request, "entrenamiento/panel.html", {
        "modelos": modelos,
        "modelo_activo": activo,
    })


@login_required
def exportar_csv(request):
    if not _puede_gestionar(request.user):
        return HttpResponseForbidden("No tienes permisos.")

    fecha_desde = request.GET.get("fecha_desde", "")
    fecha_hasta = request.GET.get("fecha_hasta", "")

    sensores = SensorLeche.objects.all()
    if fecha_desde:
        sensores = sensores.filter(
            fecha_medicion__gte=datetime.strptime(fecha_desde, "%Y-%m-%d")
        )
    if fecha_hasta:
        hasta = datetime.strptime(fecha_hasta, "%Y-%m-%d").replace(
            hour=23, minute=59, second=59
        )
        sensores = sensores.filter(fecha_medicion__lte=hasta)

    response = HttpResponse(content_type="text/csv")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    response["Content-Disposition"] = f'attachment; filename="mastitrack_datos_{ts}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "arete", "nombre", "lote", "estado_salud",
        "conteo_celulas_somaticas", "conductividad_electrica", "ph", "temperatura",
        "porcentaje_cumplimiento", "fallas_criticas",
        "diagnostico_mastitis", "fecha_medicion",
    ])

    for sensor in sensores:
        vaca = sensor.vaca
        bitacora = BitacoraOrdeno.objects(
            vaca=vaca,
            fecha_ordeno__lte=sensor.fecha_medicion,
        ).order_by("-fecha_ordeno").first()

        cumplimiento = 100.0
        fallas = 0
        if bitacora and bitacora.metricas:
            cumplimiento = bitacora.metricas.get("porcentaje_cumplimiento", 100.0)
            fallas = bitacora.metricas.get("fallas_criticas", 0)

        writer.writerow([
            vaca.arete,
            vaca.nombre,
            vaca.lote or "",
            vaca.estado_salud,
            sensor.conteo_celulas_somaticas or "",
            sensor.conductividad_electrica or "",
            sensor.ph or "",
            sensor.temperatura or "",
            cumplimiento,
            fallas,
            "" if sensor.diagnostico_mastitis is None
            else (1 if sensor.diagnostico_mastitis else 0),
            sensor.fecha_medicion.strftime("%Y-%m-%d %H:%M:%S")
            if sensor.fecha_medicion else "",
        ])

    return response


@login_required
def cargar_modelo(request):
    if not _puede_gestionar(request.user):
        return HttpResponseForbidden("No tienes permisos.")

    if request.method != "POST":
        return redirect("entrenamiento:panel")

    archivo = request.FILES.get("archivo")
    nombre = request.POST.get("nombre", "").strip()
    notas = request.POST.get("notas", "").strip()

    if not archivo or not nombre:
        messages.error(request, "Debes proporcionar un nombre y un archivo .joblib.")
        return redirect("entrenamiento:panel")

    if not archivo.name.endswith(".joblib"):
        messages.error(request, "Solo se aceptan archivos .joblib.")
        return redirect("entrenamiento:panel")

    modelos_dir = settings.MODELOS_DIR
    modelos_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{nombre.replace(' ', '_')}_{timestamp}.joblib"
    filepath = modelos_dir / filename

    with open(filepath, "wb") as f:
        for chunk in archivo.chunks():
            f.write(chunk)

    try:
        from semaforo.inference import validar_modelo
        validar_modelo(filepath)
    except Exception as e:
        filepath.unlink()
        log.error(f"Modelo rechazado '{nombre}': {e}")
        messages.error(request, f"El modelo no es valido: {e}")
        return redirect("entrenamiento:panel")

    ModeloEntrenado(
        nombre=nombre,
        archivo=filename,
        fecha_carga=datetime.now(),
        usuario=request.user.username,
        activo=False,
        notas=notas,
    ).save()

    log.info(f"Modelo '{nombre}' cargado por {request.user.username} ({filename})")
    messages.success(request, f"Modelo '{nombre}' cargado exitosamente.")
    return redirect("entrenamiento:panel")


@login_required
def activar_modelo(request, modelo_id):
    if not _puede_gestionar(request.user):
        return HttpResponseForbidden("No tienes permisos.")

    modelo = ModeloEntrenado.objects.get(id=modelo_id)

    filepath = settings.MODELOS_DIR / modelo.archivo
    if not filepath.exists():
        messages.error(request, "El archivo del modelo no se encontro en disco.")
        return redirect("entrenamiento:panel")

    try:
        from semaforo.inference import validar_modelo
        validar_modelo(filepath)
    except Exception as e:
        log.error(f"Modelo '{modelo.nombre}' no se puede activar: {e}")
        messages.error(request, f"No se puede activar: el modelo no carga correctamente. {e}")
        return redirect("entrenamiento:panel")

    ModeloEntrenado.objects.update(activo=False)
    modelo.activo = True
    modelo.save()

    from semaforo.inference import recargar_modelo
    from semaforo.services import reevaluar_todas

    recargar_modelo()
    evaluadas = reevaluar_todas(request.user.id)

    log.info(f"Modelo '{modelo.nombre}' activado por {request.user.username}, {evaluadas} vacas re-evaluadas")
    messages.success(
        request,
        f"Modelo '{modelo.nombre}' activado. {evaluadas} vaca(s) re-evaluada(s).",
    )
    return redirect("entrenamiento:panel")


@login_required
def desactivar_modelo(request, modelo_id):
    if not _puede_gestionar(request.user):
        return HttpResponseForbidden("No tienes permisos.")

    modelo = ModeloEntrenado.objects.get(id=modelo_id)
    modelo.activo = False
    modelo.save()

    from semaforo.inference import recargar_modelo
    from semaforo.services import reevaluar_todas

    recargar_modelo()
    evaluadas = reevaluar_todas(request.user.id)

    log.info(f"Modelo '{modelo.nombre}' desactivado por {request.user.username}, {evaluadas} vacas re-evaluadas")
    messages.success(
        request,
        f"Modelo '{modelo.nombre}' desactivado. Se usara el modelo base. "
        f"{evaluadas} vaca(s) re-evaluada(s).",
    )
    return redirect("entrenamiento:panel")


@login_required
def eliminar_modelo(request, modelo_id):
    if not _puede_gestionar(request.user):
        return HttpResponseForbidden("No tienes permisos.")

    modelo = ModeloEntrenado.objects.get(id=modelo_id)

    filepath = settings.MODELOS_DIR / modelo.archivo
    if filepath.exists():
        filepath.unlink()

    nombre = modelo.nombre
    era_activo = modelo.activo
    modelo.delete()

    if era_activo:
        from semaforo.inference import recargar_modelo
        from semaforo.services import reevaluar_todas

        recargar_modelo()
        evaluadas = reevaluar_todas(request.user.id)
        log.info(f"Modelo '{nombre}' eliminado (estaba activo) por {request.user.username}, {evaluadas} vacas re-evaluadas")
        messages.success(
            request,
            f"Modelo '{nombre}' eliminado. {evaluadas} vaca(s) re-evaluada(s).",
        )
    else:
        log.info(f"Modelo '{nombre}' eliminado por {request.user.username}")
        messages.success(request, f"Modelo '{nombre}' eliminado.")
    return redirect("entrenamiento:panel")
