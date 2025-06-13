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
from .pdf_generator_new import ReportePDFGenerator


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
                    foto_formset.save()
                    # Redirige a la lista de reportes del proyecto y abre el PDF en nueva ventana
                    request.session['abrir_pdf_id'] = reporte.id
                    return redirect('reportes:proyecto_detalle', proyecto_id=reporte.proyecto.id)
                else:
                    # Si hay errores en los formularios de fotos, mostrarlos
                    messages.error(request, 'Por favor corrija los errores en las imágenes.')
        else:
            foto_formset = FotoFormSet(request.POST, request.FILES)
    else:
        proyecto_id = request.GET.get('proyecto_id')
        tipo_formulario = request.GET.get('tipo_formulario')
        # Solo permitir acceso si es REPORTE FOTOGRÁFICO
        if tipo_formulario != 'REPORTE FOTOGRÁFICO':
            from django.http import Http404
            raise Http404('Solo se permite crear reportes fotográficos desde aquí.')
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

def borrar_reporte(request, reporte_id):
    reporte = get_object_or_404(ReporteFotografico, id=reporte_id)
    proyecto_id = reporte.proyecto.id
    reporte.delete()
    return redirect('reportes:proyecto_detalle', proyecto_id=proyecto_id)

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
                    'descripcion': foto.descripcion or f'Foto {i}'
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
                    form.save_m2m()  # Guardar relaciones many-to-many
                    messages.success(request, f'Proyecto "{proyecto.nombre}" creado exitosamente.')
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
            
        # Buscar el proyecto para verificar permisos
        from .models import ReporteFotografico, Proyecto
        try:
            proyecto = Proyecto.objects.get(id=proyecto_id, usuarios=request.user)
            print(f"Proyecto encontrado: {proyecto.nombre}")
        except Proyecto.DoesNotExist:
            error_msg = 'Proyecto no encontrado o sin permisos'
            print(f"Error: {error_msg}")
            return JsonResponse(
                {'error': error_msg}, 
                status=404
            )
        
        # Filtrar reportes del tipo y proyecto seleccionados
        reportes = ReporteFotografico.objects.filter(
            proyecto_id=proyecto_id,
            tipo_formulario=tipo_formulario
        ).prefetch_related('fotos').order_by('-fecha_emision')
        
        print(f"Total de reportes encontrados: {reportes.count()}")
        
        # Preparar datos de respuesta
        data = []
        for r in reportes:
            try:
                foto_principal = r.fotos.first()
                # Construir URLs usando el namespace 'reportes:'
                url_pdf = reverse('reportes:reporte_pdf', args=[r.id])
                url_editar = reverse('reportes:editar_reporte', args=[r.id])
                
                reporte_data = {
                    'id': r.id,
                    'descripcion': r.descripcion or '',
                    'fecha_emision': r.fecha_emision.strftime('%Y-%m-%d'),
                    'reporte_numero': r.reporte_numero or '',
                    'url_pdf': url_pdf,
                    'url_editar': url_editar,
                    'tipo_formulario': r.tipo_formulario,
                    'foto_principal_url': foto_principal.imagen.url if (foto_principal and hasattr(foto_principal, 'imagen')) else None,
                    'fotos_urls': [foto.imagen.url for foto in r.fotos.all()[:5] if hasattr(foto, 'imagen') and hasattr(foto.imagen, 'url')]
                }
                print(f"Reporte {r.id}: {reporte_data}")
                data.append(reporte_data)
            except Exception as e:
                error_msg = f"Error procesando reporte {r.id}: {str(e)}"
                print(error_msg)
                import traceback
                print(traceback.format_exc())
                continue
        
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