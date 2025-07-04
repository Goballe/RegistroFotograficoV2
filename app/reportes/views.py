from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.urls import reverse
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.conf import settings
from django.utils import translation
from django.utils.translation import gettext_lazy as _, activate, get_language, gettext
from django.db import transaction
from django.utils import timezone
from django.urls import reverse_lazy
from django.template.loader import get_template
import json
import os
import io
import tempfile
from io import BytesIO
from urllib.parse import urlparse

from .models import Proyecto, Usuario, TipoFormularioProyecto
from .forms import RegistroUsuarioForm, PerfilUsuarioForm, CambiarContrasenaForm, ProyectoForm


@login_required
def dashboard(request):
    """Vista principal del dashboard que muestra los proyectos del usuario."""
    if request.user.rol == Usuario.Rol.ADMIN or request.user.is_superuser:
        proyectos = Proyecto.objects.all()
    else:
        proyectos = Proyecto.objects.filter(usuarios=request.user)
    return render(request, 'reportes/dashboard.html', {'proyectos': proyectos})


@login_required
def proyecto_detalle(request, proyecto_id):
    """Vista para mostrar el detalle de un proyecto."""
    # Obtener el proyecto o retornar 404 si no existe o el usuario no tiene acceso
    proyecto = get_object_or_404(Proyecto, id=proyecto_id, usuarios=request.user)
    
    # Verificar si es una petición AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Obtener parámetros de filtrado
        data = json.loads(request.body)
        tipo_formulario = data.get('tipo_formulario')
        
        # Preparar respuesta JSON vacía ya que no hay reportes fotográficos
        return JsonResponse({'reportes': []})
    
    # Si no es AJAX, cargar la página normalmente
    context = {
        'proyecto': proyecto,
        'tipos_formulario_unicos': [],  # Ya no hay tipos de formulario de reportes fotográficos
    }
    
    return render(request, 'reportes/proyecto_detalle.html', context)


@login_required
def perfil_usuario(request):
    """Vista para editar el perfil del usuario."""
    if request.method == 'POST':
        form = PerfilUsuarioForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado correctamente.')
            return redirect('reportes:perfil')
    else:
        form = PerfilUsuarioForm(instance=request.user)
    
    return render(request, 'reportes/perfil.html', {'form': form})


@login_required
def cambiar_contrasena(request):
    """Vista para cambiar la contraseña del usuario."""
    if request.method == 'POST':
        form = CambiarContrasenaForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Contraseña cambiada correctamente.')
            return redirect('reportes:perfil')
    else:
        form = CambiarContrasenaForm(request.user)
    
    return render(request, 'reportes/cambiar_contrasena.html', {'form': form})


def registro_usuario(request):
    """Vista para registrar un nuevo usuario."""
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Cuenta creada para {username}. ¡Bienvenido!')
                return redirect('reportes:dashboard')
            else:
                messages.success(request, f'Cuenta creada para {username}. Por favor inicia sesión.')
                return redirect('login')
    else:
        form = RegistroUsuarioForm()
    return render(request, 'reportes/registro.html', {'form': form})


@login_required
def crear_proyecto(request):
    """Vista para crear un nuevo proyecto.
    Solo accesible para administradores.
    """
    if not (request.user.rol == Usuario.Rol.ADMIN or request.user.is_superuser):
        messages.error(request, 'No tienes permiso para crear proyectos.')
        return redirect('reportes:dashboard')
    
    if request.method == 'POST':
        form = ProyectoForm(request.POST, request.FILES)
        if form.is_valid():
            proyecto = form.save()
            # Asignar automáticamente al usuario que crea el proyecto
            proyecto.usuarios.add(request.user)
            # Asignar usuarios seleccionados
            if 'usuarios' in request.POST:
                for usuario_id in request.POST.getlist('usuarios'):
                    try:
                        usuario = Usuario.objects.get(id=usuario_id)
                        proyecto.usuarios.add(usuario)
                    except Usuario.DoesNotExist:
                        pass
            messages.success(request, 'Proyecto creado correctamente.')
            return redirect('reportes:listar_proyectos')
    else:
        form = ProyectoForm()
    
    # Obtener todos los usuarios para el selector
    usuarios = Usuario.objects.all().exclude(id=request.user.id)
    
    return render(request, 'reportes/crear_proyecto.html', {'form': form, 'usuarios': usuarios})


@login_required
def editar_proyecto(request, proyecto_id):
    """Vista para editar un proyecto existente.
    Solo accesible para administradores.
    """
    if not (request.user.rol == Usuario.Rol.ADMIN or request.user.is_superuser):
        messages.error(request, 'No tienes permiso para editar proyectos.')
        return redirect('reportes:dashboard')
    
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)
    
    if request.method == 'POST':
        form = ProyectoForm(request.POST, request.FILES, instance=proyecto)
        if form.is_valid():
            proyecto = form.save()
            # Actualizar usuarios
            proyecto.usuarios.clear()
            proyecto.usuarios.add(request.user)  # Asegurar que el admin actual siga teniendo acceso
            if 'usuarios' in request.POST:
                for usuario_id in request.POST.getlist('usuarios'):
                    try:
                        usuario = Usuario.objects.get(id=usuario_id)
                        proyecto.usuarios.add(usuario)
                    except Usuario.DoesNotExist:
                        pass
            messages.success(request, 'Proyecto actualizado correctamente.')
            return redirect('reportes:listar_proyectos')
    else:
        form = ProyectoForm(instance=proyecto)
    
    # Obtener todos los usuarios para el selector
    usuarios = Usuario.objects.all().exclude(id=request.user.id)
    usuarios_asignados = proyecto.usuarios.all().exclude(id=request.user.id).values_list('id', flat=True)
    
    return render(request, 'reportes/editar_proyecto.html', {
        'form': form, 
        'usuarios': usuarios,
        'usuarios_asignados': list(usuarios_asignados),
        'proyecto': proyecto
    })


@login_required
def listar_proyectos(request):
    """Vista para listar todos los proyectos.
    Solo accesible para administradores.
    """
    if not (request.user.rol == Usuario.Rol.ADMIN or request.user.is_superuser):
        messages.error(request, 'No tienes permiso para ver la lista de proyectos.')
        return redirect('reportes:dashboard')
    
    proyectos = Proyecto.objects.all().order_by('nombre')
    
    return render(request, 'reportes/listar_proyectos.html', {'proyectos': proyectos})


@login_required
def eliminar_proyecto(request, proyecto_id):
    """Vista para eliminar un proyecto existente.
    Solo accesible para administradores y requiere método POST.
    """
    if not (request.user.rol == Usuario.Rol.ADMIN or request.user.is_superuser):
        messages.error(request, 'No tienes permiso para eliminar proyectos.')
        return redirect('reportes:dashboard')
    
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)
    
    if request.method == 'POST':
        # Verificar si hay reportes asociados
        if hasattr(proyecto, 'reportes') and proyecto.reportes.exists():
            messages.error(
                request, 
                'No se puede eliminar el proyecto porque tiene reportes asociados. '
                'Elimine primero los reportes.'
            )
            return redirect('reportes:listar_proyectos')
        
        # Eliminar la imagen del proyecto si existe
        if proyecto.imagen:
            try:
                if os.path.isfile(proyecto.imagen.path):
                    os.remove(proyecto.imagen.path)
            except Exception as e:
                messages.warning(request, f'No se pudo eliminar la imagen: {str(e)}')
        
        # Eliminar el proyecto
        nombre_proyecto = proyecto.nombre
        proyecto.delete()
        messages.success(request, f'Proyecto "{nombre_proyecto}" eliminado correctamente.')
        return redirect('reportes:listar_proyectos')
    
    return render(request, 'reportes/confirmar_eliminar_proyecto.html', {'proyecto': proyecto})


@login_required
def api_reportes_por_tipo(request):
    """API para obtener reportes por tipo de formulario."""
    try:
        # Obtener parámetros
        proyecto_id = request.GET.get('proyecto_id')
        tipo_formulario = request.GET.get('tipo_formulario')
        
        if not proyecto_id or not tipo_formulario:
            return JsonResponse({'error': 'Se requieren proyecto_id y tipo_formulario'}, status=400)
        
        # Verificar que el proyecto exista y el usuario tenga acceso
        try:
            if request.user.es_administrador() or request.user.is_superuser:
                proyecto = Proyecto.objects.get(id=proyecto_id)
            else:
                proyecto = Proyecto.objects.get(id=proyecto_id, usuarios=request.user)
        except Proyecto.DoesNotExist:
            return JsonResponse({'error': 'Proyecto no encontrado o sin acceso'}, status=404)
        
        # Como ya no hay reportes fotográficos, devolvemos una lista vacía
        return JsonResponse({
            'status': 'success',
            'reportes': [],
            'count': 0,
            'proyecto': proyecto.nombre,
            'tipo_formulario': tipo_formulario
        })
        
    except Exception as e:
        import traceback
        error_msg = f"Error en api_reportes_por_tipo: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        return JsonResponse(
            {'error': 'Error interno del servidor', 'details': str(e)}, 
            status=500
        )
