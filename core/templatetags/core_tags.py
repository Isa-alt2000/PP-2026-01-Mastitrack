from django import template

register = template.Library()


@register.filter
def porcentaje(valor):
    if valor is None:
        return "0%"
    return f"{valor:.1f}%"


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
