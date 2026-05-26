def user_group(request):
    if not request.user.is_authenticated:
        return {
            "es_superadmin": False,
            "es_admin": False,
            "es_operador": False,
            "rol_usuario": "",
        }

    es_superadmin = request.user.is_superuser
    es_admin = request.user.groups.filter(name="administrador").exists()
    es_operador = request.user.groups.filter(name="operador").exists()

    if es_superadmin:
        rol_usuario = "superadmin"
    elif es_admin:
        rol_usuario = "administrador"
    elif es_operador:
        rol_usuario = "operador"
    else:
        rol_usuario = "sin rol"

    return {
        "es_superadmin": es_superadmin,
        "es_admin": es_admin,
        "es_operador": es_operador,
        "puede_gestionar": es_superadmin or es_admin,
        "rol_usuario": rol_usuario,
    }
