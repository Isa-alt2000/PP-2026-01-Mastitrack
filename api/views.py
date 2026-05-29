import json
from datetime import datetime
from functools import wraps

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from api.auth import generar_token, verificar_token
from bitacora.documents import BitacoraOrdeno, SensorLeche
from vacas.documents import Vaca


def requiere_jwt(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return JsonResponse({"error": "Token no proporcionado."}, status=401)
        payload = verificar_token(header[7:])
        if payload is None:
            return JsonResponse({"error": "Token invalido o expirado."}, status=401)
        try:
            request.api_user = User.objects.get(id=payload["user_id"])
        except User.DoesNotExist:
            return JsonResponse({"error": "Usuario no encontrado."}, status=401)
        return view_func(request, *args, **kwargs)
    return wrapper


@csrf_exempt
@require_POST
def obtener_token(request):
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "JSON invalido."}, status=400)

    username = body.get("username", "")
    password = body.get("password", "")

    user = authenticate(username=username, password=password)
    if user is None:
        return JsonResponse({"error": "Credenciales invalidas."}, status=401)

    token = generar_token(user)
    return JsonResponse({"token": token, "username": user.username})


@csrf_exempt
@require_POST
@requiere_jwt
def registrar_lecturas(request):
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "JSON invalido."}, status=400)

    lecturas = body.get("lecturas", [])
    if not lecturas:
        return JsonResponse({"error": "No se enviaron lecturas."}, status=400)

    resultados = []
    for lectura in lecturas:
        arete = lectura.get("arete", "").strip()
        if not arete:
            resultados.append({"arete": arete, "ok": False, "error": "Arete vacio."})
            continue

        try:
            vaca = Vaca.objects.get(arete=arete)
        except Vaca.DoesNotExist:
            resultados.append({"arete": arete, "ok": False, "error": "Vaca no encontrada."})
            continue

        bitacora = BitacoraOrdeno.objects(vaca=vaca).order_by("-fecha_ordeno").first()

        sensor = SensorLeche(
            vaca=vaca,
            bitacora_ordeno=bitacora,
            conteo_celulas_somaticas=lectura.get("conteo_celulas_somaticas"),
            ph=lectura.get("ph"),
            temperatura=lectura.get("temperatura"),
            conductividad_electrica=lectura.get("conductividad_electrica"),
            fecha_medicion=datetime.now(),
        )
        sensor.save()

        resultados.append({
            "arete": arete,
            "ok": True,
            "sensor_id": str(sensor.id),
            "bitacora_vinculada": str(bitacora.id) if bitacora else None,
        })

    total = len(resultados)
    exitosos = sum(1 for r in resultados if r["ok"])
    return JsonResponse({
        "total": total,
        "exitosos": exitosos,
        "fallidos": total - exitosos,
        "resultados": resultados,
    })
