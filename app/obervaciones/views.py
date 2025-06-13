from datetime import timedelta
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import os
from .observacion_pdf_generator import ObservacionPDFGenerator
from django.utils import timezone
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.views.generic.edit import FormView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.http import HttpResponseRedirect, HttpResponse
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.contrib.auth import get_user_model

from reportes.models import Proyecto
from .models import ObservacionCalidad, ObservacionSeguridadSSOMA, LevantamientoObservacion, LevantamientoSSOMA, Notificacion
from .forms import ObservacionCalidadForm, ObservacionSeguridadSSOMAForm, LevantamientoSSOMAForm, LevantamientoCalidadForm
from .utils import export_observaciones_calidad_to_excel, export_observaciones_ssoma_to_excel
from reportes.models import Proyecto


def es_editor(user):
    """Verifica si el usuario tiene el rol de editor."""
    return user.groups.filter(name='editores').exists()


def es_visor(user):
    """Verifica si el usuario tiene el rol de visor."""
    return user.groups.filter(name='visores').exists()


def puede_crear_observaciones(user):
    """Verifica si el usuario puede crear observaciones (editores)."""
    return es_editor(user)


def puede_ver_observaciones(user):
    """Verifica si el usuario puede ver observaciones (todos los usuarios autenticados)."""
    return user.is_authenticated


def puede_realizar_s(user):
    """Verifica si el usuario puede realizar s (visores)."""
    return es_visor(user)


def puede_revisar_s(user):
    """Verifica si el usuario puede revisar s (editores)."""
    return es_editor(user)


@method_decorator(csrf_exempt, name='dispatch')
class GetRandomTableView(View):
    """
    Vista que devuelve un DataFrame aleatorio en formato JSON.
    """
    def get(self, request, *args, **kwargs):
        try:
            print("=== Iniciando GetRandomTableView ===")
            # Generar el DataFrame aleatorio
            random_df = generate_random_df()
            print("DataFrame generado:", random_df)
            
            # Convertir el DataFrame a un diccionario
            data = random_df.to_dict(orient='records')
            
            # Obtener los nombres de las columnas para el DataTable
            columns = [{'data': col, 'title': col.upper()} for col in random_df.columns]
            
            response_data = {
                'status': 'success',
                'data': data,
                'columns': columns
            }
            
            print("Enviando respuesta:", response_data)
            
            return JsonResponse(response_data)
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)

    def post(self, request, *args, **kwargs):
        try:
            # Si necesitas manejar solicitudes POST en el futuro
            data = json.loads(request.body)
            return JsonResponse({'status': 'success', 'data': data})
            
        except json.JSONDecodeError:
            return JsonResponse(
                {'status': 'error', 'message': 'Formato JSON inválido'}, 
                status=400
            )
        except Exception as e:
            return JsonResponse(
                {'status': 'error', 'message': str(e)}, 
                status=500
            )


class TablaObservacionesView(LoginRequiredMixin, View):
    """
    Vista para redirigir a la nueva interfaz de observaciones de calidad.
    Mantenida por compatibilidad con enlaces existentes.
    """
    def get(self, request, *args, **kwargs):
        proyecto_id = request.GET.get('proyecto_id')
        if proyecto_id:
            # Redirigir a la nueva vista de lista de observaciones
            return redirect('obervaciones:lista_observaciones', proyecto_id=proyecto_id)
        # Si no hay proyecto_id, redirigir al dashboard
        return redirect('reportes:dashboard')


@method_decorator(login_required, name='dispatch')
class ListaObservacionesCalidadView(LoginRequiredMixin, ListView):
    """
    Vista para listar todas las observaciones de calidad de un proyecto.
    Los visores solo ven las observaciones que tienen asignadas.
    """
    model = ObservacionCalidad
    template_name = 'obervaciones/lista_observaciones_calidad.html'
    context_object_name = 'observaciones'
    paginate_by = 10
    
    def get_queryset(self):
        self.proyecto = get_object_or_404(Proyecto, id=self.kwargs['proyecto_id'])
        queryset = ObservacionCalidad.objects.filter(proyecto=self.proyecto)
        
        # Si el usuario es visor, solo puede ver las observaciones que le asignaron
        if es_visor(self.request.user):
            queryset = queryset.filter(asignado_a=self.request.user)
            
        return queryset.order_by('-fecha', 'item')
    
    def get_proyecto(self):
        return self.proyecto
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['proyecto'] = self.get_proyecto()
        context['es_editor'] = es_editor(self.request.user)
        return context


@method_decorator(login_required, name='dispatch')
class CrearObservacionCalidadView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    Vista para crear una nueva observación de calidad.
    Solo disponible para usuarios con rol de editor.
    """
    model = ObservacionCalidad
    form_class = ObservacionCalidadForm
    template_name = 'obervaciones/observacion_calidad_form.html'
    
    def test_func(self):
        return puede_crear_observaciones(self.request.user)
    
    def handle_no_permission(self):
        messages.error(self.request, 'No tiene permiso para crear observaciones.')
        return redirect('obervaciones:lista_observaciones', proyecto_id=self.kwargs['proyecto_id'])
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['proyecto'] = get_object_or_404(Proyecto, id=self.kwargs['proyecto_id'])
        kwargs['usuario'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'La observación se ha creado correctamente.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('obervaciones:lista_observaciones', kwargs={
            'proyecto_id': self.kwargs['proyecto_id']
        })
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['proyecto'] = get_object_or_404(Proyecto, id=self.kwargs['proyecto_id'])
        context['titulo'] = 'Nueva Observación de Calidad'
        context['es_editor'] = True
        return context


@method_decorator(login_required, name='dispatch')
class EditarObservacionCalidadView(LoginRequiredMixin, UpdateView):
    """
    Vista para editar una observación de calidad existente.
    """
    model = ObservacionCalidad
    form_class = ObservacionCalidadForm
    template_name = 'obervaciones/observacion_calidad_form.html'
    pk_url_kwarg = 'observacion_id'
    
    def get_queryset(self):
        return ObservacionCalidad.objects.filter(proyecto_id=self.kwargs['proyecto_id'])
    
    def get_success_url(self):
        return reverse('obervaciones:lista_observaciones', kwargs={
            'proyecto_id': self.kwargs['proyecto_id']
        })
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['proyecto'] = get_object_or_404(Proyecto, id=self.kwargs['proyecto_id'])
        context['titulo'] = 'Editar Observación de Calidad'
        context['editar'] = True
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'La observación se ha actualizado correctamente.')
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class EliminarObservacionCalidadView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    Vista para eliminar una observación de calidad.
    Solo disponible para usuarios con rol de editor.
    """
    model = ObservacionCalidad
    pk_url_kwarg = 'observacion_id'
    template_name = 'obervaciones/confirmar_eliminar_observacion.html'
    
    def test_func(self):
        return puede_crear_observaciones(self.request.user)
    
    def handle_no_permission(self):
        messages.error(self.request, 'No tiene permiso para eliminar observaciones.')
        return redirect('obervaciones:lista_observaciones', proyecto_id=self.kwargs['proyecto_id'])
    
    def get_queryset(self):
        # Permitir que cualquier editor pueda eliminar observaciones
        return ObservacionCalidad.objects.filter(
            proyecto_id=self.kwargs['proyecto_id']
        )
    
    def get_success_url(self):
        messages.success(self.request, 'La observación se ha eliminado correctamente.')
        return reverse('obervaciones:lista_observaciones', kwargs={
            'proyecto_id': self.kwargs['proyecto_id']
        })
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['proyecto'] = get_object_or_404(Proyecto, id=self.kwargs['proyecto_id'])
        context['es_editor'] = True
        return context


@method_decorator(login_required, name='dispatch')
class DetalleObservacionCalidadView(LoginRequiredMixin, DetailView):
    """
    Vista para ver los detalles de una observación de calidad.
    Los visores solo ven las observaciones que tienen asignadas.
    """
    model = ObservacionCalidad
    template_name = 'obervaciones/detalle_observacion.html'
    pk_url_kwarg = 'observacion_id'
    context_object_name = 'observacion'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(proyecto_id=self.kwargs['proyecto_id'])
        
        # Si el usuario es visor, solo puede ver las observaciones que le asignaron
        if es_visor(self.request.user):
            queryset = queryset.filter(asignado_a=self.request.user)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        observacion = self.get_object()
        context['proyecto'] = observacion.proyecto
        
        # Verificar roles de usuario
        context['es_editor'] = es_editor(self.request.user)
        context['es_visor'] = es_visor(self.request.user)
        
        # Indicar que NO es una observación SSOMA
        context['es_ssoma'] = False
        
        # Información de levantamiento (si existe)
        # Intentamos obtener el levantamiento de dos formas diferentes para asegurar que lo encontramos
        try:
            levantamiento = LevantamientoObservacion.objects.filter(observacion=observacion).first()
            tiene_lev = levantamiento is not None
        except:
            tiene_lev = hasattr(observacion, 'levantamiento')
            levantamiento = observacion.levantamiento if tiene_lev else None
        
        context['tiene_levantamiento'] = tiene_lev
        if tiene_lev:
            context['levantamiento'] = levantamiento
        
        return context


# ---------------------------------------------------------------------------
# Vistas de LEVANTAMIENTOS – Calidad
# ---------------------------------------------------------------------------

class CrearLevantamientoCalidadView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Permite a usuarios VISOR crear el levantamiento de una observación de calidad."""

    def test_func(self):
        return es_visor(self.request.user)

    def get_observacion(self):
        return get_object_or_404(
            ObservacionCalidad,
            pk=self.kwargs['observacion_id'],
            proyecto_id=self.kwargs['proyecto_id'],
        )

    def get(self, request, *args, **kwargs):
        observacion = self.get_observacion()
        if hasattr(observacion, 'levantamiento'):
            # Si el levantamiento fue rechazado, permitir crear uno nuevo
            if observacion.levantamiento.estado == 'Rechazado':
                # Eliminar el levantamiento anterior
                levantamiento_anterior = observacion.levantamiento
                levantamiento_anterior.delete()
                messages.info(request, 'El levantamiento anterior fue rechazado. Por favor, cree uno nuevo.')
                form = LevantamientoCalidadForm()
            else:
                messages.info(request, 'Esta observación ya tiene levantamiento registrado.')
                return redirect('obervaciones:ver_observacion', proyecto_id=observacion.proyecto.id, observacion_id=observacion.id)
        else:
            form = LevantamientoCalidadForm()
        
        return render(request, 'obervaciones/levantamiento_form.html', {
            'form': form,
            'proyecto': observacion.proyecto,
            'observacion': observacion,
            'es_visor': True,
        })

    def post(self, request, *args, **kwargs):
        observacion = self.get_observacion()
        form = LevantamientoCalidadForm(request.POST, request.FILES)
        if form.is_valid():
            lev = form.save(commit=False)
            lev.observacion = observacion
            lev.creado_por = request.user
            
            # Calcular el tiempo de levantamiento automáticamente
            from datetime import datetime
            fecha_observacion = observacion.fecha
            fecha_levantamiento = lev.fecha_levantamiento or datetime.now().date()
            
            # Calcular la diferencia en días
            diferencia_dias = (fecha_levantamiento - fecha_observacion).days
            
            # Formatear como HH:MM:SS (considerando solo días como horas)
            tiempo_formato = f"{diferencia_dias:02d}:00:00"
            lev.tiempo_levantamiento = tiempo_formato
            
            lev.save()

            # notificar a editores
            url = reverse('obervaciones:revisar_levantamiento_calidad', kwargs={'proyecto_id': observacion.proyecto.id, 'levantamiento_id': lev.id})
            mensaje = f'Nuevo levantamiento pendiente de revisión para la observación {observacion.item}'
            _crear_notificaciones_para_editores(mensaje, url)

            messages.success(request, 'Levantamiento enviado correctamente.')
            return redirect('obervaciones:lista_observaciones', proyecto_id=observacion.proyecto.id)
        return render(request, 'obervaciones/levantamiento_form.html', {
            'form': form,
            'proyecto': observacion.proyecto,
            'observacion': observacion,
            'es_visor': True,
        })


class RevisarLevantamientoCalidadView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Permite a usuarios EDITOR aprobar o rechazar el levantamiento."""

    model = LevantamientoObservacion
    template_name = 'obervaciones/revisar_levantamiento.html'
    pk_url_kwarg = 'levantamiento_id'
    fields = ['estado', 'comentario_revisor']

    def test_func(self):
        return es_editor(self.request.user)
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        levantamiento = self.get_object()
        observacion = levantamiento.observacion
        proyecto = observacion.proyecto
        
        context['observacion'] = observacion
        context['proyecto'] = proyecto
        context['es_editor'] = es_editor(self.request.user)
        
        return context

    def form_valid(self, form):
        # Guardar el levantamiento con el revisor
        lev = form.save(commit=False)
        lev.revisor = self.request.user
        lev.revisado_en = timezone.now()
        lev.save()
        
        # Actualizar el estado de la observación según el estado del levantamiento
        observacion = lev.observacion
        
        if lev.estado == 'Aprobado':
            # Actualizar directamente en la base de datos para evitar problemas de caché
            ObservacionCalidad.objects.filter(id=observacion.id).update(estado='Atendido')
            messages.success(self.request, f"Levantamiento aprobado. La observación {observacion.item} ha sido marcada como atendida.")
        elif lev.estado == 'Rechazado':
            ObservacionCalidad.objects.filter(id=observacion.id).update(estado='Pendiente')
            messages.warning(self.request, f"Levantamiento rechazado. La observación {observacion.item} sigue pendiente.")
        
        # Notificar al visor responsable
        try:
            url = reverse('obervaciones:ver_observacion', kwargs={'proyecto_id': lev.observacion.proyecto.id, 'observacion_id': lev.observacion.id})
            mensaje = f'Su levantamiento de la observación {lev.observacion.item} ha sido {lev.get_estado_display().lower()}.'
            Notificacion.objects.create(usuario=lev.creado_por, mensaje=mensaje, url=url)
        except Exception:
            pass
            
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('obervaciones:lista_observaciones', kwargs={'proyecto_id': self.object.observacion.proyecto.id})

# =============================================
# Vistas para Observaciones de Seguridad SSOMA
# =============================================

class ListaObservacionesSSOMAView(LoginRequiredMixin, ListView):
    """
    Vista para listar todas las observaciones de seguridad de un proyecto.
    Los supervisores solo ven las observaciones que tienen asignadas.
    """
    model = ObservacionSeguridadSSOMA
    template_name = 'obervaciones/lista_observaciones_ssoma.html'
    context_object_name = 'observaciones'
    paginate_by = 10

    def get_queryset(self):
        self.proyecto = get_object_or_404(Proyecto, id=self.kwargs.get('proyecto_id'))
        queryset = ObservacionSeguridadSSOMA.objects.filter(proyecto=self.proyecto)
        
        # Si el usuario no es editor, solo ver las observaciones asignadas
        if not (self.request.user.is_superuser or self.request.user.groups.filter(name='editores').exists()):
            queryset = queryset.filter(asignado_a=self.request.user)
            
        return queryset.select_related('proyecto', 'asignado_a', 'creado_por').order_by('-fecha')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['proyecto'] = self.proyecto
        context['es_editor'] = self.request.user.groups.filter(name='editores').exists()
        context['es_visor'] = self.request.user.groups.filter(name='visores').exists()
        context['es_ssoma'] = True  # Para identificar que es la vista de SSOMA
        
        # Obtener IDs de observaciones con s pendientes de revisión
        if context['es_editor']:
            context['s_pendientes_ids'] = []  # No aplica para SSOMA
            
        return context


class CrearObservacionSSOMAView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    Vista para crear una nueva observación de seguridad.
    Solo disponible para usuarios con rol de administrador o supervisor.
    """
    model = ObservacionSeguridadSSOMA
    form_class = ObservacionSeguridadSSOMAForm
    template_name = 'obervaciones/observacion_ssoma_form.html'

    def test_func(self):
        return self.request.user.groups.filter(name='editores').exists()
    
    def handle_no_permission(self):
        messages.error(self.request, 'No tiene permiso para realizar esta acción. Se requiere ser miembro del grupo "editores".')
        return redirect('home')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['proyecto'] = get_object_or_404(Proyecto, id=self.kwargs.get('proyecto_id'))
        kwargs['usuario'] = self.request.user
        return kwargs
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        User = get_user_model()
        form.fields['asignado_a'].queryset = User.objects.filter(
            groups__name='visores', is_active=True
        ).order_by('first_name', 'last_name')
        return form

    def form_valid(self, form):
        form.instance.proyecto = get_object_or_404(Proyecto, id=self.kwargs.get('proyecto_id'))
        form.instance.creado_por = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, 'Observación de seguridad creada exitosamente.')
        return response

    def get_success_url(self):
        return reverse('obervaciones:lista_observaciones_ssoma', kwargs={'proyecto_id': self.kwargs.get('proyecto_id')})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        proyecto_id = self.kwargs.get('proyecto_id')
        context['proyecto'] = get_object_or_404(Proyecto, id=proyecto_id)
        context['titulo'] = 'Nueva Observación de Seguridad'
        context['es_editor'] = self.request.user.groups.filter(name='editores').exists()
        context['es_ssoma'] = True  # Para identificar que es SSOMA
        return context


class EditarObservacionSSOMAView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Vista para editar una observación de seguridad existente.
    Solo disponible para usuarios con rol de administrador o supervisor asignado.
    """
    model = ObservacionSeguridadSSOMA
    form_class = ObservacionSeguridadSSOMAForm
    template_name = 'obervaciones/observacion_ssoma_form.html'
    pk_url_kwarg = 'pk'

    def test_func(self):
        # Solo los editores pueden editar las observaciones SSOMA
        return self.request.user.groups.filter(name='editores').exists()
    
    def handle_no_permission(self):
        messages.error(self.request, 'No tiene permiso para editar esta observación.')
        return redirect('home')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        User = get_user_model()
        form.fields['asignado_a'].queryset = User.objects.filter(
            groups__name='visores', is_active=True
        ).order_by('first_name', 'last_name')
        return form

    def get_queryset(self):
        return ObservacionSeguridadSSOMA.objects.filter(proyecto_id=self.kwargs.get('proyecto_id'))

    def get_success_url(self):
        messages.success(self.request, 'Observación de seguridad actualizada exitosamente.')
        return reverse('obervaciones:lista_observaciones_ssoma', kwargs={
            'proyecto_id': self.kwargs.get('proyecto_id')
        })

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['proyecto'] = get_object_or_404(Proyecto, id=self.kwargs.get('proyecto_id'))
        context['titulo'] = 'Editar Observación de Seguridad'
        context['es_editor'] = self.request.user.groups.filter(name='administradores').exists()
        context['edicion'] = True
        context['es_ssoma'] = True  # Para identificar que es SSOMA
        return context


class EliminarObservacionSSOMAView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    Vista para eliminar una observación de seguridad.
    Solo disponible para usuarios con rol de administrador.
    """
    model = ObservacionSeguridadSSOMA
    pk_url_kwarg = 'pk'
    template_name = 'obervaciones/confirmar_eliminar_observacion.html'

    def test_func(self):
        return self.request.user.groups.filter(name='editores').exists()
    
    def handle_no_permission(self):
        messages.error(self.request, 'No tiene permiso para eliminar observaciones.')
        return redirect('home')

    def get_queryset(self):
        return ObservacionSeguridadSSOMA.objects.filter(proyecto_id=self.kwargs.get('proyecto_id'))

    def get_success_url(self):
        messages.success(self.request, 'Observación de seguridad eliminada exitosamente.')
        return reverse('obervaciones:lista_observaciones_ssoma', kwargs={'proyecto_id': self.kwargs.get('proyecto_id')})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['proyecto'] = get_object_or_404(Proyecto, id=self.kwargs.get('proyecto_id'))
        context['es_ssoma'] = True  # Para identificar que es SSOMA
        return context


class DetalleObservacionSSOMAView(LoginRequiredMixin, DetailView):
    """
    Vista para ver los detalles de una observación de seguridad.
    Los supervisores solo ven las observaciones que tienen asignadas.
    """
    model = ObservacionSeguridadSSOMA
    template_name = 'obervaciones/detalle_observacion.html'
    pk_url_kwarg = 'pk'
    context_object_name = 'observacion'

    def get_queryset(self):
        proyecto_id = self.kwargs.get('proyecto_id')
        queryset = ObservacionSeguridadSSOMA.objects.filter(proyecto_id=proyecto_id)
        
        # Si no es administrador, solo puede ver las observaciones que le han asignado
        if not (self.request.user.is_superuser or 
               self.request.user.groups.filter(name='administradores').exists()):
            queryset = queryset.filter(asignado_a=self.request.user)
            
        return queryset.select_related('proyecto', 'asignado_a', 'creado_por')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['proyecto'] = get_object_or_404(Proyecto, id=self.kwargs.get('proyecto_id'))
        context['es_editor'] = self.request.user.groups.filter(name='administradores').exists()
        context['es_ssoma'] = True  # Para identificar que es SSOMA
        return context


@login_required
def generar_pdf_observacion(request, proyecto_id, observacion_id):
    """Genera un PDF para una observación de calidad."""
    # Obtener la observación o retornar 404 si no existe
    observacion = get_object_or_404(
        ObservacionCalidad, 
        id=observacion_id, 
        proyecto__id=proyecto_id
    )
    
    try:
        # Crear el generador de PDF
        pdf_generator = ObservacionPDFGenerator()
        
        # Generar el PDF
        pdf_content = pdf_generator.generate_pdf_calidad(observacion)
        
        # Configurar la respuesta HTTP con el PDF
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="observacion_calidad_{observacion.id}.pdf"'
        return response
        
    except Exception as e:
        # En caso de error, registrar el error y mostrar mensaje al usuario
        import traceback
        error_msg = f'Error al generar el PDF: {str(e)}'
        print(error_msg)
        traceback.print_exc()
        messages.error(request, error_msg)
        # Redirigir a la página de detalle de la observación
        return redirect('obervaciones:ver_observacion', proyecto_id=proyecto_id, observacion_id=observacion_id)

def home(request):
    return HttpResponse("Página de inicio de observaciones")

def about(request):
    return render(request, 'obervaciones/about.html', {'title': 'Acerca de'})
