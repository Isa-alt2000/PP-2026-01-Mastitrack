from django.urls import path

from bitacora import views

app_name = "bitacora"

urlpatterns = [
    path("", views.lista_bitacoras, name="lista"),
    path("crear/", views.crear_bitacora, name="crear"),
    path("<str:bitacora_id>/", views.detalle_bitacora, name="detalle"),
    path("<str:bitacora_id>/sensor/", views.registrar_sensor, name="registrar_sensor"),
    path("api/resumen/<str:vaca_id>/", views.api_bitacora_resumen, name="api_resumen"),
]
