from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.urls import reverse
from django.http import JsonResponse
import json
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.conf import settings
from django.utils import translation
from django.utils.translation import gettext_lazy as _, activate, get_language, gettext
from django.db import transaction
from django.utils import timezone
from django.urls import reverse_lazy
from django.template.loader import get_template
from .models import Proyecto, ReporteFotografico, FotoReporte, Usuario, TipoFormularioProyecto
from .forms import ReporteForm, RegistroUsuarioForm, FotoFormSet, PerfilUsuarioForm, CambiarContrasenaForm, ProyectoForm
from weasyprint import HTML
import os
from urllib.parse import urlparse
import io
import tempfile
from io import BytesIO
from .reporte_pdf_generator import ReportePDFGenerator


@login_required
def dashboard(request):
    if request.user.rol == Usuario.Rol.ADMIN or request.user.is_superuser:
        proyectos = Proyecto.objects.all()
    else:
        proyectos = Proyecto.objects.filter(usuarios=request.user)
    return render(request, 'reportes/dashboard.html', {'proyectos': proyectos})


from django.core.paginator import Paginator
from django.db.models import Q

@login_required
def proyecto_detalle(request, proyecto_id):
    # Obtener el proyecto o retornar 404 si no existe o el usuario no tiene acceso
    proyecto = get_object_or_404(Proyecto, id=proyecto_id, usuarios=request.user)
    
    # Verificar si es una petición AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Obtener parámetros de filtrado
        data = json.loads(request.body)
        tipo_formulario = data.get('tipo_formulario', 'REPORTE FOTOGRÁFICO')
        
        # Obtener reportes filtrados
        reportes = proyecto.reportes.filter(tipo_formulario=tipo_formulario).order_by('-fecha_emision')
        
        # Preparar datos para la respuesta JSON
        reportes_data = []
        for reporte in reportes:
            reportes_data.append({
                'id': reporte.id,
                'reporte_numero': reporte.reporte_numero,
                'fecha_emision': reporte.fecha_emision.strftime('%Y-%m-%d'),
                'descripcion': reporte.descripcion,
                'fotos_urls': [foto.imagen.url for foto in reporte.fotos.all()],
                'url_pdf': f'/reportes/pdf/{reporte.id}/',
                'url_editar': f'/reportes/editar/{reporte.id}/',
            })
        
        return JsonResponse({'reportes': reportes_data})
    
    # Si no es AJAX, cargar la página normalmente
    tipo_formulario = request.GET.get('tipo_formulario', 'REPORTE FOTOGRÁFICO')
    
    # Obtener tipos de formulario únicos para el selector
    tipos_formulario_unicos = list(proyecto.reportes.values_list('tipo_formulario', flat=True).distinct())
    
    context = {
        'proyecto': proyecto,
        'tipos_formulario_unicos': tipos_formulario_unicos,
        'tipo_formulario_actual': tipo_formulario,
    }
    
    return render(request, 'reportes/proyecto_detalle.html', context)


@login_required
def editar_reporte(request, reporte_id):
    reporte = get_object_or_404(ReporteFotografico, id=reporte_id)
    if not (request.user.rol in [Usuario.Rol.ADMIN, Usuario.Rol.EDITOR] or request.user.is_superuser):
        return HttpResponseForbidden('No tienes permiso para editar este reporte.')

    if request.method == 'POST':
        form = ReporteForm(request.POST, request.FILES, instance=reporte)
        foto_formset = FotoFormSet(request.POST, request.FILES, instance=reporte)
        if form.is_valid() and foto_formset.is_valid():
            with transaction.atomic():
                form.save()
                foto_formset.save()
                messages.success(request, 'Reporte actualizado correctamente.')
                return redirect('reportes:proyecto_detalle', proyecto_id=reporte.proyecto.id)
    else:
        form = ReporteForm(instance=reporte)
        foto_formset = FotoFormSet(instance=reporte)

    return render(request, 'reportes/crear_reporte.html', {
        'form': form,
        'foto_formset': foto_formset,
        'proyecto': reporte.proyecto,
        'proyecto_id': reporte.proyecto.id,
        'edit_mode': True,
        'reporte': reporte,
    })

@login_required
def crear_reporte(request):
    # Verificar si el usuario tiene permiso para crear reportes
    if request.user.rol == 'VISOR':
        messages.error(request, 'No tienes permiso para crear reportes.')
        return redirect('reportes:dashboard')
        
    proyecto_id = (
        request.GET.get('proyecto_id')
        or request.GET.get('proyecto')
        or request.POST.get('proyecto')
    )
    proyecto_instance = None
    if proyecto_id:
        try:
            proyecto_instance = Proyecto.objects.get(id=proyecto_id)
        except Proyecto.DoesNotExist:
            proyecto_instance = None
    
    # Get the next report number for this project and report type
    def get_next_report_number(proyecto, tipo_formulario):
        last_report = ReporteFotografico.objects.filter(
            proyecto=proyecto,
            tipo_formulario=tipo_formulario
        ).order_by('-reporte_numero').first()
        return (last_report.reporte_numero + 1) if last_report else 1

    if request.method == 'POST':
        form = ReporteForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                reporte = form.save(commit=False)
                if proyecto_instance:
                    reporte.proyecto = proyecto_instance
                # Toma el tipo_formulario enviado por GET o POST
                tipo_formulario = request.GET.get('tipo_formulario') or request.POST.get('tipo_formulario') or 'REPORTE FOTOGRÁFICO'
                reporte.tipo_formulario = tipo_formulario
                reporte.save()
                
                foto_formset = FotoFormSet(request.POST, request.FILES, instance=reporte)
                if foto_formset.is_valid():
                    # Guardar el formset
                    instances = foto_formset.save(commit=False)
                    for instance in instances:
                        # Asignar el reporte a cada instancia de foto
                        instance.reporte = reporte
                        instance.save()
                    
                    # Eliminar las fotos marcadas para borrar
                    for obj in foto_formset.deleted_objects:
                        obj.delete()
                    
                    # Redirige a la lista de reportes del proyecto con mensaje de éxito
                    request.session['abrir_pdf_id'] = reporte.id
                    messages.success(request, f'Reporte {reporte.tipo_formulario} creado exitosamente con {len(instances)} imágenes.')
                    return redirect('reportes:lista_reportes_fotograficos', proyecto_id=reporte.proyecto.id)
                else:
                    # Si hay errores en los formularios de fotos, mostrarlos
                    for error in foto_formset.errors:
                        if error:
                            messages.error(request, f'Error en las imágenes: {error}')
                            break
        else:
            foto_formset = FotoFormSet(request.POST, request.FILES)
    else:
        proyecto_id = request.GET.get('proyecto_id')
        tipo_formulario = request.GET.get('tipo_formulario')
        # Validar que el tipo de formulario sea uno de los permitidos
        tipos_permitidos = ['REPORTE FOTOGRÁFICO', 'CONTROL DE OBS CALIDAD', 'OBSERVACIONES', 'CONTROL DE OBS SSOMA']
        if tipo_formulario not in tipos_permitidos:
            from django.http import Http404
            raise Http404(f'Solo se permite crear reportes de los siguientes tipos: {", ".join(tipos_permitidos)}.')
        if proyecto_instance:
            # Get the next report number
            tipo_formulario = tipo_formulario or 'REPORTE FOTOGRÁFICO'
            next_report_number = get_next_report_number(proyecto_instance, tipo_formulario)
            
            # Set initial data with project info and default values
            initial_data = {
                'proyecto': proyecto_instance,
                'cliente': proyecto_instance.cliente,
                'contratista': proyecto_instance.contratista,
                'codigo_proyecto': proyecto_instance.codigo_proyecto,
                'inicio_supervision': proyecto_instance.inicio_supervision,
                'fecha_emision': timezone.now().date(),
                'elaborado_por': f"{request.user.first_name} {request.user.last_name}".strip(),
                'revisado_por': '',  # Se deja en blanco para que el usuario lo complete
                # Se dejan en blanco para que el usuario los complete
                'reporte_numero': '',
                'version_reporte': '',
                'mes_actual_obra': 1  # Valor por defecto, se puede cambiar
            }
            
            if tipo_formulario:
                initial_data['tipo_formulario'] = tipo_formulario
                
            form = ReporteForm(initial=initial_data)
            form.fields['proyecto'].initial = proyecto_instance
            from django import forms as django_forms
            # Configurar campos ocultos
            form.fields['proyecto'].widget = django_forms.HiddenInput()
            form.fields['tipo_formulario'].widget = django_forms.HiddenInput()
            
            # Hacer que algunos campos sean de solo lectura ya que se llenan automáticamente
            for field in ['cliente', 'contratista', 'codigo_proyecto']:
                form.fields[field].widget.attrs['readonly'] = True
            
            # Asegurarse de que version_reporte sea editable
            if 'version_reporte' in form.fields:
                form.fields['version_reporte'].widget.attrs.pop('readonly', None)
                form.fields['version_reporte'].widget.attrs['class'] = 'form-control'
        else:
            form = ReporteForm()
        foto_formset = FotoFormSet(queryset=FotoReporte.objects.none())
    
    context = {
        'form': form,
        'foto_formset': foto_formset,
    }
    
    if proyecto_instance:
        context['proyecto'] = proyecto_instance
        context['proyecto_id'] = proyecto_instance.id
    else:
        context['proyecto_id'] = proyecto_id
        
    return render(request, 'reportes/crear_reporte.html', context)

@login_required
def lista_reportes(request):
    # Obtener todos los proyectos del usuario
    proyectos = Proyecto.objects.filter(usuarios=request.user)
    
    # Obtener parámetros de filtrado
    proyecto_id = request.GET.get('proyecto_id')
    tipo_formulario = request.GET.get('tipo_formulario')
    
    # Inicializar queryset de reportes
    reportes = ReporteFotografico.objects.prefetch_related('fotos').filter(proyecto__usuarios=request.user)
    
    # Aplicar filtros
    if proyecto_id and proyecto_id.isdigit():
        proyecto_id = int(proyecto_id)
        reportes = reportes.filter(proyecto_id=proyecto_id)
        
        # Obtener tipos de formulario únicos para el proyecto seleccionado
        try:
            proyecto = Proyecto.objects.get(id=proyecto_id)
            tipos_formulario_unicos = list(proyecto.reportes.values_list('tipo_formulario', flat=True).distinct())
            
            # Filtrar por tipo de formulario si se especifica
            if tipo_formulario:
                reportes = reportes.filter(tipo_formulario=tipo_formulario)
                
        except Proyecto.DoesNotExist:
            tipos_formulario_unicos = []
    else:
        tipos_formulario_unicos = []
    
    # Ordenar por fecha de emisión descendente
    reportes = reportes.order_by('-fecha_emision')
    
    # Paginación
    paginator = Paginator(reportes, 10)  # 10 reportes por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'reportes/lista_reportes.html', {
        'reportes': page_obj,
        'tipos_formulario_unicos': tipos_formulario_unicos,
        'proyectos': proyectos,
        'proyecto_id': int(proyecto_id) if (proyecto_id and proyecto_id.isdigit()) else None,
        'tipo_formulario_actual': tipo_formulario,
    })

@login_required
def ver_reporte(request, reporte_id):
    """
    Vista para mostrar el detalle de un reporte con sus imágenes.
    """
    # Obtener el reporte o retornar 404 si no existe o el usuario no tiene acceso
    reporte = get_object_or_404(ReporteFotografico, id=reporte_id, proyecto__usuarios=request.user)
    
    # Obtener las fotos del reporte ordenadas
    fotos = reporte.fotos.all().order_by('orden')
    
    context = {
        'reporte': reporte,
        'fotos': fotos,
        'proyecto': reporte.proyecto,
    }
    
    return render(request, 'reportes/ver_reporte.html', context)


@login_required
def borrar_reporte(request, reporte_id):
    reporte = get_object_or_404(ReporteFotografico, id=reporte_id)
    proyecto_id = reporte.proyecto.id
    reporte_tipo = reporte.tipo_formulario
    reporte.delete()
    messages.success(request, f'Reporte {reporte_tipo} eliminado exitosamente.')
    return redirect('reportes:lista_reportes_fotograficos', proyecto_id=proyecto_id)

@login_required
def perfil_usuario(request):
    if request.method == 'POST':
        form = PerfilUsuarioForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _('Tu perfil ha sido actualizado correctamente.'))
            return redirect('reportes:perfil_usuario')
    else:
        form = PerfilUsuarioForm(instance=request.user)
    
    return render(request, 'registration/perfil.html', {
        'form': form,
        'active_tab': 'perfil'
    })

@login_required
def cambiar_contrasena(request):
    if request.method == 'POST':
        form = CambiarContrasenaForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, _('Tu contraseña ha sido cambiada exitosamente.'))
            return redirect('reportes:perfil_usuario')
    else:
        form = CambiarContrasenaForm(request.user)
    
    return render(request, 'registration/cambiar_contrasena.html', {
        'form': form,
        'active_tab': 'contrasena'
    })

def registro_usuario(request):
    if request.user.is_authenticated:
        return redirect('perfil_usuario')
        
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password1'])
            user.save()
            
            # Autenticar al usuario después del registro
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, '¡Registro exitoso! Ahora estás conectado.')
                return redirect('home')
    else:
        form = RegistroUsuarioForm()
    
    return render(request, 'registration/registro.html', {'form': form})

@login_required
def reporte_pdf(request, reporte_id):
    # Obtener el reporte o retornar 404 si no existe o el usuario no tiene acceso
    reporte = get_object_or_404(ReporteFotografico, id=reporte_id, proyecto__usuarios=request.user)
    
    try:
        # Obtener las fotos del reporte
        fotos = []
        for i, foto in enumerate(reporte.fotos.all().order_by('orden'), 1):
            # Construir la ruta completa al archivo de imagen
            if foto.imagen:
                imagen_path = os.path.join(settings.MEDIA_ROOT, str(foto.imagen))
                fotos.append({
                    'imagen_path': imagen_path,
                    'descripcion': foto.descripcion or ''
                })
        
        # Crear el generador de PDF sin buffer inicial
        pdf_generator = ReportePDFGenerator()
        
        # Generar el PDF (esto creará su propio buffer)
        pdf_content = pdf_generator.generate_pdf(reporte, fotos)
        
        # Configurar la respuesta HTTP con el PDF
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="reporte_{reporte.id}.pdf"'
        return response
        
    except Exception as e:
        # En caso de error, registrar el error y mostrar mensaje al usuario
        import traceback
        error_msg = f'Error al generar el PDF: {str(e)}'
        print(error_msg)
        traceback.print_exc()
        messages.error(request, error_msg)
        # Redirigir a la página de detalle del proyecto
        return redirect('reportes:proyecto_detalle', proyecto_id=reporte.proyecto_id)

@login_required
def crear_proyecto(request):
    """
    Vista para crear un nuevo proyecto.
    Solo accesible para administradores.
    """
    if not (request.user.rol == Usuario.Rol.ADMIN or request.user.is_superuser):
        messages.error(request, 'No tienes permiso para realizar esta acción.')
        return redirect('reportes:dashboard')
    
    if request.method == 'POST':
        form = ProyectoForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    proyecto = form.save(commit=False)
                    proyecto.save()
                    
                    # Asignar automáticamente el acceso al administrador que crea el proyecto
                    proyecto.usuarios.add(request.user)
                    
                    form.save_m2m()  # Guardar relaciones many-to-many
                    messages.success(request, f'Proyecto "{proyecto.nombre}" creado exitosamente. Ahora tienes acceso a este proyecto.')
                    return redirect('reportes:editar_proyecto', proyecto_id=proyecto.id)
            except Exception as e:
                messages.error(request, f'Error al guardar el proyecto: {str(e)}')
        else:
            messages.error(request, 'Por favor, corrija los errores en el formulario.')
    else:
        form = ProyectoForm()
    
    return render(request, 'reportes/crear_proyecto.html', {
        'form': form,
        'titulo': 'Nuevo Proyecto'
    })

@login_required
def editar_proyecto(request, proyecto_id):
    """
    Vista para editar un proyecto existente.
    Solo accesible para administradores.
    """
    if not (request.user.rol == Usuario.Rol.ADMIN or request.user.is_superuser):
        messages.error(request, 'No tienes permiso para realizar esta acción.')
        return redirect('reportes:dashboard')
    
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)
    
    if request.method == 'POST':
        form = ProyectoForm(request.POST, request.FILES, instance=proyecto)
        if form.is_valid():
            try:
                with transaction.atomic():
                    proyecto = form.save()
                    messages.success(request, f'Proyecto "{proyecto.nombre}" actualizado exitosamente.')
                    return redirect('reportes:editar_proyecto', proyecto_id=proyecto.id)
            except Exception as e:
                messages.error(request, f'Error al actualizar el proyecto: {str(e)}')
        else:
            messages.error(request, 'Por favor, corrija los errores en el formulario.')
    else:
        form = ProyectoForm(instance=proyecto)
    
    return render(request, 'reportes/crear_proyecto.html', {
        'form': form,
        'proyecto': proyecto,
        'titulo': 'Editar Proyecto'
    })

@login_required
def listar_proyectos(request):
    """
    Vista para listar todos los proyectos.
    Solo accesible para administradores.
    """
    if not (request.user.rol == Usuario.Rol.ADMIN or request.user.is_superuser):
        messages.error(request, 'No tienes permiso para acceder a esta sección.')
        return redirect('reportes:dashboard')
    
    try:
        proyectos = Proyecto.objects.all().order_by('-id')
        return render(request, 'reportes/listar_proyectos.html', {
            'proyectos': proyectos,
            'total_proyectos': proyectos.count()
        })
    except Exception as e:
        messages.error(request, f'Error al cargar la lista de proyectos: {str(e)}')
        return redirect('reportes:dashboard')

@login_required
def eliminar_proyecto(request, proyecto_id):
    """
    Vista para eliminar un proyecto existente.
    Solo accesible para administradores y requiere método POST.
    """
    if not (request.user.rol == Usuario.Rol.ADMIN or request.user.is_superuser):
        messages.error(request, 'No tienes permiso para realizar esta acción.')
        return redirect('reportes:dashboard')
    
    if request.method != 'POST':
        messages.error(request, 'Método no permitido.')
        return redirect('reportes:listar_proyectos')
    
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)
    proyecto_nombre = proyecto.nombre
    
    try:
        with transaction.atomic():
            # Verificar si el proyecto tiene reportes asociados
            if proyecto.reportes.exists():
                messages.warning(
                    request, 
                    f'No se puede eliminar el proyecto "{proyecto_nombre}" porque tiene reportes asociados.'
                )
                return redirect('reportes:listar_proyectos')
            
            proyecto.delete()
            messages.success(request, f'El proyecto "{proyecto_nombre}" ha sido eliminado correctamente.')
    except Exception as e:
        messages.error(
            request, 
            f'Error al eliminar el proyecto "{proyecto_nombre}": {str(e)}'
        )
    
    return redirect('reportes:listar_proyectos')

@login_required
def api_reportes_por_tipo(request):
    try:
        print("\n=== Iniciando api_reportes_por_tipo ===")
        print(f"Método: {request.method}")
        print(f"Headers: {request.headers}")
        print(f"Usuario: {request.user}")
        print(f"Parámetros GET: {request.GET}")
        
        # Obtener parámetros
        proyecto_id = request.GET.get('proyecto_id')
        tipo_formulario = request.GET.get('tipo_formulario')
        
        print(f"Proyecto ID: {proyecto_id}, Tipo: {tipo_formulario}")
        
        # Validar parámetros
        if not (proyecto_id and tipo_formulario):
            error_msg = 'Se requieren los parámetros proyecto_id y tipo_formulario'
            print(f"Error: {error_msg}")
            return JsonResponse(
                {'error': error_msg}, 
                status=400
            )
            
        # Obtener el proyecto y verificar permisos
        proyecto = get_object_or_404(Proyecto, id=proyecto_id)
        if request.user not in proyecto.usuarios.all() and not request.user.is_superuser:
            return JsonResponse(
                {'error': 'No tienes permiso para acceder a este proyecto'}, 
                status=403
            )
        
        # Obtener los reportes del tipo especificado
        reportes = ReporteFotografico.objects.filter(
            proyecto_id=proyecto_id,
            tipo_formulario__iexact=tipo_formulario
        ).order_by('-fecha_creacion')
        
        # Formatear los datos para la respuesta
        data = []
        for reporte in reportes:
            reporte_data = {
                'id': reporte.id,
                'titulo': reporte.titulo or 'Sin título',
                'fecha_creacion': reporte.fecha_creacion.strftime('%d/%m/%Y %H:%M'),
                'descripcion': reporte.descripcion or '',
                'usuario': reporte.usuario.get_full_name() or reporte.usuario.username,
                'tipo_formulario': reporte.tipo_formulario,
                'url_editar': reverse('reportes:editar_reporte', args=[reporte.id]),
                'url_pdf': reverse('reportes:reporte_pdf', args=[reporte.id]),
            }
            
            # Agregar la primera imagen si existe
            primera_imagen = reporte.fotos.first()
            if primera_imagen and hasattr(primera_imagen, 'imagen'):
                reporte_data['imagen_url'] = request.build_absolute_uri(primera_imagen.imagen.url)
            
            data.append(reporte_data)
        
        response_data = {
            'status': 'success',
            'reportes': data,
            'count': len(data),
            'proyecto': proyecto.nombre,
            'tipo_formulario': tipo_formulario
        }
        
        print(f"=== Respuesta: {response_data}")
        return JsonResponse(response_data)
        
    except Exception as e:
        import traceback
        error_msg = f"Error en api_reportes_por_tipo: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        return JsonResponse(
            {'error': 'Error interno del servidor', 'details': str(e)}, 
            status=500
        )


@login_required
def lista_reportes_fotograficos(request, proyecto_id):
    """
    Vista para mostrar la lista de reportes fotográficos de un proyecto.
    """
    # Obtener el proyecto y verificar permisos
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)
    if request.user not in proyecto.usuarios.all() and not request.user.is_superuser:
        messages.error(request, 'No tienes permiso para acceder a este proyecto.')
        return redirect('reportes:dashboard')
    
    # Obtener los parámetros de filtrado
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    # Obtener el número de reporte (secuencial) y convertirlo a entero si existe
    numero_reporte = request.GET.get('numero_reporte')
    if numero_reporte:
        try:
            numero_reporte = int(numero_reporte)
        except (ValueError, TypeError):
            numero_reporte = None
    
    # Construir la consulta base
    reportes = ReporteFotografico.objects.filter(
        proyecto=proyecto,
        tipo_formulario__iexact='REPORTE FOTOGRÁFICO'
    )
    
    # Aplicar filtros
    if fecha_desde:
        reportes = reportes.filter(creado_en__date__gte=fecha_desde)
    if fecha_hasta:
        # Añadir 1 día para incluir el día completo de la fecha hasta
        from datetime import datetime, timedelta
        fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d') + timedelta(days=1)
        reportes = reportes.filter(creado_en__date__lte=fecha_hasta_dt.date())
        
    # Convertir el queryset a lista para poder filtrar por posición
    reportes_lista = list(reportes.order_by('-creado_en'))
    
    # Aplicar filtro por número de reporte (secuencial)
    if numero_reporte and isinstance(numero_reporte, int):
        if 1 <= numero_reporte <= len(reportes_lista):
            # Mantener solo el reporte en la posición indicada (restamos 1 porque las listas empiezan en 0)
            reportes_lista = [reportes_lista[numero_reporte - 1]]
        else:
            # Si el número está fuera de rango, devolver lista vacía
            reportes_lista = []
    
    # Convertir de vuelta a queryset para mantener la compatibilidad con el resto del código
    from django.db.models import Q
    if reportes_lista:
        reportes = reportes.filter(id__in=[r.id for r in reportes_lista])
    else:
        reportes = reportes.none()
        
    # Ordenar por fecha de creación descendente
    reportes = reportes.order_by('-creado_en')
    
    # Agregar la URL de la primera imagen a cada reporte
    for reporte in reportes:
        primera_imagen = reporte.fotos.first()
        if primera_imagen and hasattr(primera_imagen, 'imagen'):
            reporte.imagen_principal = primera_imagen.imagen
    
    context = {
        'proyecto': proyecto,
        'reportes': reportes,
        'filtro_fecha_desde': fecha_desde if fecha_desde else '',
        'filtro_fecha_hasta': fecha_hasta if fecha_hasta else '',
        'filtro_numero_reporte': numero_reporte if numero_reporte else '',
    }
    
    return render(request, 'reportes/lista_reportes_fotograficos.html', context)