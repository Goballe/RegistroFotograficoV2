from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import JsonResponse
import json
from datetime import datetime
from django.db.models.functions import ExtractYear, ExtractMonth
from reportes.models import Usuario
from obervaciones.models import ObservacionCalidad, ObservacionSeguridadSSOMA

@login_required
def dashboard_graficos(request):
    """
    Vista para mostrar gráficos de estadísticas de observaciones.
    Solo accesible para administradores.
    """
    # Verificar si el usuario es administrador
    if not (request.user.rol == Usuario.Rol.ADMIN or request.user.is_superuser):
        return render(request, 'reportes/acceso_denegado.html', {
            'mensaje': 'No tienes permiso para acceder a esta sección.',
            'redireccion': 'reportes:dashboard'
        })
    
    # Obtener el año seleccionado (por defecto el año actual)
    anio_seleccionado = request.GET.get('anio', datetime.now().year)
    try:
        anio_seleccionado = int(anio_seleccionado)
    except (ValueError, TypeError):
        anio_seleccionado = datetime.now().year
        
    # Obtener años disponibles para el selector
    anios_disponibles = obtener_anios_disponibles()
    
    # Obtener datos para los gráficos
    datos_graficos = json.dumps({
        'calidad': obtener_datos_calidad(anio_seleccionado),
        'ssoma': obtener_datos_ssoma(anio_seleccionado),
        'anio_seleccionado': anio_seleccionado,
        'anios_disponibles': anios_disponibles
    })
    
    return render(request, 'reportes/dashboard_graficos.html', {
        'datos_graficos': datos_graficos,
        'anio_seleccionado': anio_seleccionado,
        'anios_disponibles': anios_disponibles
    })

@login_required
def api_datos_graficos(request):
    """
    API para obtener datos de gráficos en formato JSON.
    Solo accesible para administradores.
    """
    if not (request.user.rol == Usuario.Rol.ADMIN or request.user.is_superuser):
        return JsonResponse({'error': 'Acceso denegado'}, status=403)
    
    tipo = request.GET.get('tipo', 'todos')
    
    # Obtener el año seleccionado
    anio_seleccionado = request.GET.get('anio', datetime.now().year)
    try:
        anio_seleccionado = int(anio_seleccionado)
    except (ValueError, TypeError):
        anio_seleccionado = datetime.now().year
    
    if tipo == 'calidad':
        datos = obtener_datos_calidad(anio_seleccionado)
    elif tipo == 'ssoma':
        datos = obtener_datos_ssoma(anio_seleccionado)
    else:
        datos = {
            'calidad': obtener_datos_calidad(anio_seleccionado),
            'ssoma': obtener_datos_ssoma(anio_seleccionado),
            'anio_seleccionado': anio_seleccionado,
            'anios_disponibles': obtener_anios_disponibles()
        }
    
    return JsonResponse(datos)

def obtener_anios_disponibles():
    """Obtiene los años disponibles para los que hay observaciones."""
    # Obtener años únicos de observaciones de calidad
    anios_calidad = ObservacionCalidad.objects.annotate(
        anio=ExtractYear('fecha')
    ).values_list('anio', flat=True).distinct()
    
    # Obtener años únicos de observaciones SSOMA
    anios_ssoma = ObservacionSeguridadSSOMA.objects.annotate(
        anio=ExtractYear('fecha')
    ).values_list('anio', flat=True).distinct()
    
    # Combinar y ordenar los años
    anios = sorted(set(list(anios_calidad) + list(anios_ssoma)))
    
    # Si no hay años, incluir el año actual
    if not anios:
        anios = [datetime.now().year]
        
    return anios

def obtener_datos_mensuales(queryset, anio):
    """Obtiene datos mensuales para un queryset y año específico."""
    datos_mensuales = queryset.filter(
        fecha__year=anio
    ).annotate(
        mes=ExtractMonth('fecha')
    ).values('mes').annotate(
        total=Count('id')
    ).order_by('mes')
    
    # Crear un diccionario con todos los meses (1-12)
    meses_completos = {i: 0 for i in range(1, 13)}
    
    # Llenar con los datos reales
    for dato in datos_mensuales:
        meses_completos[dato['mes']] = dato['total']
    
    # Convertir a lista de diccionarios para JSON
    resultado = [
        {'mes': mes, 'total': total}
        for mes, total in meses_completos.items()
    ]
    
    return resultado

def obtener_datos_calidad(anio=None):
    """Obtiene datos de observaciones de calidad para gráficos."""
    # Si no se especifica año, usar todos los datos
    queryset = ObservacionCalidad.objects.all()
    if anio:
        queryset = queryset.filter(fecha__year=anio)
    
    # Datos por estado
    estados = queryset.values('estado').annotate(
        total=Count('id')
    ).order_by('estado')
    
    # Datos por nivel de riesgo
    niveles_riesgo = queryset.values('nivel_riesgo').annotate(
        total=Count('id')
    ).order_by('nivel_riesgo')
    
    # Datos por estado y nivel de riesgo
    estado_riesgo = []
    for estado in ObservacionCalidad.EstadoObservacion.values:
        por_riesgo = []
        for riesgo in ObservacionCalidad.NivelRiesgo.values:
            count = queryset.filter(
                estado=estado, nivel_riesgo=riesgo
            ).count()
            por_riesgo.append({
                'riesgo': riesgo,
                'total': count
            })
        estado_riesgo.append({
            'estado': estado,
            'datos': por_riesgo
        })
    
    # Datos mensuales si se especificó un año
    datos_mensuales = []
    if anio:
        datos_mensuales = obtener_datos_mensuales(ObservacionCalidad.objects.all(), anio)
    
    return {
        'estados': list(estados),
        'niveles_riesgo': list(niveles_riesgo),
        'estado_riesgo': estado_riesgo,
        'datos_mensuales': datos_mensuales
    }

def obtener_datos_ssoma(anio=None):
    """Obtiene datos de observaciones SSOMA para gráficos."""
    # Si no se especifica año, usar todos los datos
    queryset = ObservacionSeguridadSSOMA.objects.all()
    if anio:
        queryset = queryset.filter(fecha__year=anio)
    
    # Datos por estado
    estados = queryset.values('estado').annotate(
        total=Count('id')
    ).order_by('estado')
    
    # Datos por nivel de riesgo
    niveles_riesgo = queryset.values('nivel_riesgo').annotate(
        total=Count('id')
    ).order_by('nivel_riesgo')
    
    # Datos por estado y nivel de riesgo
    estado_riesgo = []
    for estado in ObservacionSeguridadSSOMA.EstadoObservacion.values:
        por_riesgo = []
        for riesgo in ObservacionSeguridadSSOMA.NivelRiesgo.values:
            count = queryset.filter(
                estado=estado, nivel_riesgo=riesgo
            ).count()
            por_riesgo.append({
                'riesgo': riesgo,
                'total': count
            })
        estado_riesgo.append({
            'estado': estado,
            'datos': por_riesgo
        })
    
    # Datos mensuales si se especificó un año
    datos_mensuales = []
    if anio:
        datos_mensuales = obtener_datos_mensuales(ObservacionSeguridadSSOMA.objects.all(), anio)
    
    return {
        'estados': list(estados),
        'niveles_riesgo': list(niveles_riesgo),
        'estado_riesgo': estado_riesgo,
        'datos_mensuales': datos_mensuales
    }
