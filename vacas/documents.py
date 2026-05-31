import mongoengine as me

ESTADOS_SALUD = ("Sano", "Observacion", "Enferma", "Tratamiento", "Aislado")
TIPOS_CONSULTA = ("Rutinaria", "Emergencia", "Seguimiento")
ESTADOS_DIAGNOSTICO_MASTITIS = (
    "confirmado",
    "sospecha_calculada",
    "sospecha_descartada",
)


class Vaca(me.Document):
    arete = me.StringField(required=True, unique=True)
    nombre = me.StringField(required=True)
    fecha_nacimiento = me.DateTimeField()
    lote = me.StringField()
    estado_salud = me.StringField(choices=ESTADOS_SALUD, default="Sano")
    diagnostico_mastitis = me.StringField(
        choices=ESTADOS_DIAGNOSTICO_MASTITIS, null=True, default=None
    )
    fecha_aislamiento = me.DateTimeField()
    activa = me.BooleanField(default=True)
    razon_baja = me.StringField()

    meta = {"collection": "vacas", "ordering": ["arete"]}

    def __str__(self):
        return f"{self.arete} - {self.nombre}"

    @property
    def edad_display(self):
        if not self.fecha_nacimiento:
            return "Sin dato"
        from datetime import datetime
        delta = datetime.now() - self.fecha_nacimiento
        anios = delta.days // 365
        meses = (delta.days % 365) // 30
        return f"{anios}a {meses}m"


class VisitaVeterinaria(me.Document):
    vaca = me.ReferenceField(Vaca, required=True)
    fecha_visita = me.DateTimeField(required=True)
    tipo_consulta = me.StringField(choices=TIPOS_CONSULTA, default="Rutinaria")
    aplica_tratamiento = me.BooleanField(default=False)
    tratamiento = me.StringField()
    observaciones = me.StringField()
    costo_total_cifrado = me.StringField()

    meta = {"collection": "visitas_veterinarias", "ordering": ["-fecha_visita"]}

    def __str__(self):
        return f"Visita {self.vaca.arete} - {self.fecha_visita}"

    def set_costo(self, valor: float):
        from core.crypto import cifrar
        self.costo_total_cifrado = cifrar(str(valor))

    def get_costo(self) -> float:
        if not self.costo_total_cifrado:
            return 0.0
        from core.crypto import descifrar
        return float(descifrar(self.costo_total_cifrado))
