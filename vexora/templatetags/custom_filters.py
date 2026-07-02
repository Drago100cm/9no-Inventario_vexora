from django import template

register = template.Library()

@register.filter
def sum(value, arg):
    """
    Suma los valores de un atributo en una lista de objetos.
    """
    try:
        return sum(getattr(item, arg, 0) for item in value)
    except (TypeError, ValueError):
        return 0