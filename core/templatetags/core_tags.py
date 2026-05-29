from django import template

register = template.Library()


@register.filter
def porcentaje(valor):
    if valor is None:
        return "0%"
    return f"{valor:.1f}%"


@register.filter
def prob_display(valor):
    """Muestra probabilidad (0-1) como porcentaje con 4 decimales."""
    if valor is None:
        return "0.0000%"
    return f"{valor * 100:.4f}%"


@register.filter
def color_alerta(nivel):
    colores = {
        "verde": "#009288",
        "amarillo": "#BC955C",
        "rojo": "#9F2241",
    }
    return colores.get(nivel, "#98989A")


@register.filter
def moneda(valor):
    if valor is None:
        return "$0.00"
    return f"${valor:,.2f}"
