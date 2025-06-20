from django import template
from django.template.defaultfilters import stringfilter
from django.utils.translation import gettext_lazy as _
import math

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

@register.filter
def intdiv(value, arg):
    """Divide el valor por el argumento y devuelve un entero."""
    try:
        return math.ceil(int(value) / int(arg))
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def get_range(value, start=0):
    """Crea un rango de números desde start hasta value."""
    try:
        start = int(start)
        value = int(value)
        return range(start, value + 1)
    except (ValueError, TypeError):
        return range(0)

@register.filter
def add(value, arg):
    """Suma el valor y el argumento."""
    try:
        return int(value) + int(arg)
    except (ValueError, TypeError):
        return value
