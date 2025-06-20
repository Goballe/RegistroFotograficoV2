from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from obervaciones.models import Notificacion, ObservacionCalidad, ObservacionSeguridadSSOMA
from django.utils import timezone
from datetime import timedelta

@login_required
def obtener_notificaciones(request):
    """
    Vista para obtener las notificaciones del usuario actual.
    Retorna JSON con las notificaciones no leídas y el conteo.
    """
    # Obtener notificaciones no leídas del usuario actual
    notificaciones = Notificacion.objects.filter(
        usuario=request.user,
        leida=False
    ).order_by('-creada_en')[:5]  # Limitamos a las 5 más recientes
    
    # Contar observaciones pendientes asignadas al usuario
    observaciones_calidad = ObservacionCalidad.objects.filter(
        asignado_a=request.user,
        estado=ObservacionCalidad.EstadoObservacion.PENDIENTE
    ).count()
    
    observaciones_ssoma = ObservacionSeguridadSSOMA.objects.filter(
        asignado_a=request.user,
        estado=ObservacionSeguridadSSOMA.EstadoObservacion.PENDIENTE
    ).count()
    
    # Preparar datos para el JSON
    notificaciones_data = []
    for notif in notificaciones:
        notificaciones_data.append({
            'id': notif.id,
            'mensaje': notif.mensaje,
            'url': notif.url,
            'creada_en': notif.creada_en.strftime('%d/%m/%Y %H:%M')
        })
    
    # Total de notificaciones no leídas
    total_no_leidas = notificaciones.count()
    
    # Total de observaciones pendientes
    total_observaciones = observaciones_calidad + observaciones_ssoma
    
    return JsonResponse({
        'notificaciones': notificaciones_data,
        'total_no_leidas': total_no_leidas,
        'total_observaciones': total_observaciones,
        'total': total_no_leidas + total_observaciones
    })

@login_required
def marcar_como_leida(request, notificacion_id):
    """
    Vista para marcar una notificación como leída.
    """
    notificacion = get_object_or_404(Notificacion, id=notificacion_id, usuario=request.user)
    notificacion.leida = True
    notificacion.save()
    
    return JsonResponse({'success': True})

@login_required
def marcar_todas_como_leidas(request):
    """
    Vista para marcar todas las notificaciones como leídas.
    """
    Notificacion.objects.filter(usuario=request.user, leida=False).update(leida=True)
    
    return JsonResponse({'success': True})

@login_required
def todas_las_notificaciones(request):
    """
    Vista para mostrar todas las notificaciones en una página completa.
    """
    # Obtener todas las notificaciones del usuario, ordenadas por fecha (más recientes primero)
    notificaciones = Notificacion.objects.filter(usuario=request.user).order_by('-creada_en')
    
    # Obtener observaciones pendientes asignadas al usuario
    observaciones_calidad = ObservacionCalidad.objects.filter(
        asignado_a=request.user,
        estado=ObservacionCalidad.EstadoObservacion.PENDIENTE
    ).order_by('-creado_en')
    
    observaciones_ssoma = ObservacionSeguridadSSOMA.objects.filter(
        asignado_a=request.user,
        estado=ObservacionSeguridadSSOMA.EstadoObservacion.PENDIENTE
    ).order_by('-creado_en')
    
    # Calcular fechas para agrupar notificaciones
    hoy = timezone.now().date()
    ayer = hoy - timedelta(days=1)
    semana_pasada = hoy - timedelta(days=7)
    
    context = {
        'notificaciones': notificaciones,
        'observaciones_calidad': observaciones_calidad,
        'observaciones_ssoma': observaciones_ssoma,
        'hoy': hoy,
        'ayer': ayer,
        'semana_pasada': semana_pasada,
    }
    
    # Marcar notificaciones como leídas al verlas
    if request.GET.get('marcar_leidas', 'true') == 'true':
        notificaciones.filter(leida=False).update(leida=True)
    
    return render(request, 'reportes/todas_notificaciones.html', context)
