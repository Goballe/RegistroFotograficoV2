from django import template
import os

register = template.Library()

@register.filter(name='filename')
def filename(value):
    """
    Returns the filename from a file path
    """
    if not value:
        return ''
    return os.path.basename(str(value))
