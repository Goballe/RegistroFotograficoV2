from django import template
from django.template.defaultfilters import stringfilter
from django.utils.translation import gettext_lazy as _

register = template.Library()

@register.filter
def batch(iterable, n=1):
    """
    Divide un iterable en grupos de tamaño n.
    Útil para mostrar elementos en filas de n columnas.
    """
    length = len(iterable)
    for ndx in range(0, length, n):
        yield iterable[ndx:min(ndx + n, length)]

@register.filter
def multiply(value, arg):
    """Multiplica el valor por el argumento."""
    try:
        return int(value) * int(arg)
    except (ValueError, TypeError):
        try:
            return value * int(arg)
        except (ValueError, TypeError):
            return ''
