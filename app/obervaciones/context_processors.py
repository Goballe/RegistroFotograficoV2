from django.contrib.auth.decorators import login_required


def notificaciones(request):
    """Proporciona notificaciones no leídas para el usuario autenticado."""
    if request.user.is_authenticated:
        pendientes = request.user.notificaciones.filter(leida=False)[:5]
        return {"notificaciones_pendientes": pendientes}
    return {}
