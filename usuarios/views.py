from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render


def requiere_gestion(view_func):
    def wrapper(request, *args, **kwargs):
        if not (request.user.is_superuser or request.user.groups.filter(name="administrador").exists()):
            return HttpResponseForbidden("No tienes permisos para acceder a esta seccion.")
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


@login_required
@requiere_gestion
def lista_usuarios(request):
    usuarios = User.objects.all().order_by("username")
    return render(request, "usuarios/lista.html", {"usuarios": usuarios})


@login_required
@requiere_gestion
def crear_usuario(request):
    grupos = Group.objects.all()
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        nombre = request.POST.get("first_name", "")
        apellido = request.POST.get("last_name", "")
        email = request.POST.get("email", "")
        grupo_id = request.POST.get("grupo")

        if User.objects.filter(username=username).exists():
            return render(request, "usuarios/form_usuario.html", {
                "grupos": grupos,
                "error": "El nombre de usuario ya existe.",
            })

        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=nombre,
            last_name=apellido,
            email=email,
        )

        if grupo_id:
            grupo = Group.objects.get(id=grupo_id)
            user.groups.add(grupo)

        return redirect("usuarios:lista")

    return render(request, "usuarios/form_usuario.html", {"grupos": grupos})


@login_required
@requiere_gestion
def editar_usuario(request, user_id):
    usuario = get_object_or_404(User, id=user_id)
    grupos = Group.objects.all()

    if request.method == "POST":
        usuario.first_name = request.POST.get("first_name", "")
        usuario.last_name = request.POST.get("last_name", "")
        usuario.email = request.POST.get("email", "")
        usuario.is_active = request.POST.get("is_active") == "on"

        password = request.POST.get("password", "")
        if password:
            usuario.set_password(password)

        usuario.save()

        grupo_id = request.POST.get("grupo")
        usuario.groups.clear()
        if grupo_id:
            grupo = Group.objects.get(id=grupo_id)
            usuario.groups.add(grupo)

        return redirect("usuarios:lista")

    grupo_actual = usuario.groups.first()
    return render(request, "usuarios/form_usuario.html", {
        "usuario": usuario,
        "grupos": grupos,
        "grupo_actual": grupo_actual,
        "editando": True,
    })
