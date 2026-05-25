def user_group(request):
    if not request.user.is_authenticated:
        return {"es_admin": False, "es_operador": False}
    return {
        "es_admin": request.user.groups.filter(name="administrador").exists(),
        "es_operador": request.user.groups.filter(name="operador").exists(),
    }
