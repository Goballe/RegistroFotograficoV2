from django import template
from datetime import timedelta

register = template.Library()

@register.filter
def format_tiempo_levantamiento(tiempo):
    """
    Formatea el tiempo de levantamiento:
    - Si es menos de 1 día, muestra en horas
    - Si son 2 o más días, muestra en días
    """
    if not tiempo:
        return "-"
    
    # Convertir a días y horas
    total_seconds = tiempo.total_seconds()
    days = total_seconds // (24 * 3600)
    hours = (total_seconds % (24 * 3600)) // 3600
    
    # Si son 2 o más días, mostrar solo días
    if days >= 2:
        return f"{int(days)} días"
    
    # Si es menos de 1 día, mostrar en horas
    elif days < 1:
        # Calcular minutos para mostrar formato HH:MM
        minutes = (total_seconds % 3600) // 60
        return f"{int(hours)}h {int(minutes)}m"
    
    # Si es exactamente 1 día o entre 1 y 2 días
    else:
        if hours == 0:
            return f"{int(days)} día"
        else:
            return f"{int(days)} día {int(hours)}h"
