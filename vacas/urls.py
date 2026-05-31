from django.urls import path

from vacas import views

app_name = "vacas"

urlpatterns = [
    path("", views.lista_vacas, name="lista"),
    path("crear/", views.crear_vaca, name="crear"),
    path("<str:vaca_id>/", views.detalle_vaca, name="detalle"),
    path("<str:vaca_id>/editar/", views.editar_vaca, name="editar"),
    path("<str:vaca_id>/visita/", views.crear_visita, name="crear_visita"),
    path("<str:vaca_id>/sensor/", views.registrar_sensor_vaca, name="registrar_sensor"),
    path("<str:vaca_id>/confirmar-mastitis/", views.confirmar_mastitis, name="confirmar_mastitis"),
    path("<str:vaca_id>/descartar-mastitis/", views.descartar_mastitis, name="descartar_mastitis"),
    path("<str:vaca_id>/limpiar-diagnostico/", views.limpiar_diagnostico, name="limpiar_diagnostico"),
    path("api/por-lote/", views.api_vacas_lote, name="api_por_lote"),
]
