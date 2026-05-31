import mongoengine as me


class ModeloEntrenado(me.Document):
    nombre = me.StringField(required=True)
    archivo = me.StringField(required=True)
    fecha_carga = me.DateTimeField(required=True)
    usuario = me.StringField()
    activo = me.BooleanField(default=False)
    notas = me.StringField()

    meta = {
        "collection": "modelos_entrenados",
        "ordering": ["-fecha_carga"],
    }

    def __str__(self):
        return f"{self.nombre} ({'activo' if self.activo else 'inactivo'})"
