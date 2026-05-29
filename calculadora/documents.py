import mongoengine as me


class ParametrosFinancieros(me.Document):
    fecha_actualizacion = me.DateTimeField(required=True)
    modificado_por = me.StringField()

    precios_insumos = me.DictField(default=lambda: {
        "sellador_yodo_litro": 120.50,
        "toallas_paquete": 85.00,
        "prueba_cmt": 45.00,
    })

    costos_reaccion = me.DictField(default=lambda: {
        "precio_promedio_antibiotico": 850.00,
        "costo_promedio_consulta_vet": 600.00,
        "costo_reemplazo_vaca": 35000.00,
    })

    valor_produccion = me.DictField(default=lambda: {
        "precio_venta_litro_leche": 11.50,
        "produccion_promedio_vaca_dia": 25.0,
    })

    meta = {
        "collection": "parametros_financieros",
        "ordering": ["-fecha_actualizacion"],
    }

    def __str__(self):
        return f"Parametros ({self.fecha_actualizacion})"

    @classmethod
    def obtener_vigentes(cls):
        params = cls.objects.first()
        if not params:
            from datetime import datetime
            params = cls(fecha_actualizacion=datetime.now())
            params.save()
        return params
