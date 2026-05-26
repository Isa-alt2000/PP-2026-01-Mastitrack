from django.urls import path

from usuarios import views

app_name = "usuarios"

urlpatterns = [
    path("", views.lista_usuarios, name="lista"),
    path("crear/", views.crear_usuario, name="crear"),
    path("<int:user_id>/editar/", views.editar_usuario, name="editar"),
]
