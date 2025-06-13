from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from datetime import timedelta
from django.http import HttpResponseRedirect, HttpResponse
import os
from django.contrib.auth.decorators import login_required
from .observacion_pdf_generator import ObservacionPDFGenerator

from .models import ObservacionSeguridadSSOMA, LevantamientoSSOMA
from .forms import ObservacionSeguridadSSOMAForm, LevantamientoSSOMAForm
from reportes.models import Proyecto

def es_administrador(user):
    return user.groups.filter(name='administradores').exists()

def es_supervisor(user):
    return user.groups.filter(name='supervisores').exists()

class ListaObservacionesSSOMAView(LoginRequiredMixin, ListView):
    model = ObservacionSeguridadSSOMA
    template_name = 'obervaciones/lista_observaciones_ssoma.html'
    context_object_name = 'observaciones'
    paginate_by = 10
    
    def get_queryset(self):
        self.proyecto = get_object_or_404(Proyecto, id=self.kwargs['proyecto_id'])
        queryset = ObservacionSeguridadSSOMA.objects.filter(proyecto=self.proyecto)
        if not (self.request.user.is_superuser or es_administrador(self.request.user)):
            queryset = queryset.filter(asignado_a=self.request.user)
        return queryset.order_by('-fecha', 'item')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['proyecto'] = self.proyecto
        context['es_editor'] = es_administrador(self.request.user) or self.request.user.is_superuser
        context['es_visor'] = not context['es_editor']
        context['es_ssoma'] = True
        return context

class CrearObservacionSSOMAView(LoginRequiredMixin, CreateView):
    model = ObservacionSeguridadSSOMA
    form_class = ObservacionSeguridadSSOMAForm
    template_name = 'obervaciones/observacion_ssoma_form.html'

    def dispatch(self, request, *args, **kwargs):
        print(f"DEBUG: Método de solicitud: {request.method}")
        print(f"DEBUG: Ruta: {request.path}")
        print(f"DEBUG: Usuario: {request.user}")
        # Permitir solo a superuser, admin o supervisor
        if not (request.user.is_superuser or es_administrador(request.user) or es_supervisor(request.user) or request.user.groups.filter(name='visores').exists()):
            messages.error(request, 'No tiene permisos para crear observaciones de seguridad.')
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
        
    def post(self, request, *args, **kwargs):
        # Asegurarse de que self.object exista para SingleObjectMixin
        self.object = None
        print("DEBUG: Método POST recibido")
        print("DEBUG: Datos POST:", request.POST)
        print("DEBUG: Archivos:", request.FILES)
        
        # Obtener el proyecto
        proyecto = self.get_proyecto()
        print(f"DEBUG: Proyecto obtenido: {proyecto.id} - {proyecto.nombre}")
        
        # Inicializar campos faltantes con valores predeterminados
        data = request.POST.copy()
        
        # Verificar y establecer campos requeridos si no están presentes
        required_fields = {
            'item': 'SSO-001',
            'tipo_observacion': 'Acto Inseguro',
            'area': 'Operaciones',
            'semana_obs': f'Semana {timezone.now().date().isocalendar()[1]}',
            'fecha': timezone.now().date().strftime('%Y-%m-%d'),
            'punto_inspeccion': 'Área de Trabajo',
            'subclasificacion': 'Procedimiento de Trabajo',
            'nivel_riesgo': 'Medio',
            'estado': 'Pendiente'
        }
        
        # Verificar cada campo requerido
        for field, default_value in required_fields.items():
            if not data.get(field):
                print(f"DEBUG: Campo {field} no presente, estableciendo valor predeterminado: {default_value}")
                data[field] = default_value
        
        # Crear un nuevo formulario con los datos completados
        form = self.form_class(data, request.FILES, proyecto=proyecto, usuario=request.user)
        print("DEBUG: Formulario creado con datos completados")
        
        if form.is_valid():
            print("DEBUG: Formulario válido después de completar campos")
            try:
                # Asignar proyecto y usuario creador
                form.instance.proyecto = proyecto
                form.instance.creado_por = request.user
                
                # Establecer tiempo_levantamiento a 0 si el modelo lo requiere y está vacío
                if hasattr(form.instance, 'tiempo_levantamiento') and not form.instance.tiempo_levantamiento:
                    form.instance.tiempo_levantamiento = timedelta()
                
                # Guardar el formulario
                self.object = form.save()
                print(f"DEBUG: Observación SSOMA guardada correctamente con ID: {self.object.id}")
                
                # Mensaje de éxito
                messages.success(request, 'Observación de seguridad creada correctamente.')
                
                # Redireccionar a la página de detalle
                return HttpResponseRedirect(self.get_success_url())
            except Exception as e:
                print(f"DEBUG: Error al guardar la observación SSOMA: {str(e)}")
                messages.error(request, f"Error al guardar: {str(e)}")
                return self.form_invalid(form)
        else:
            # Imprimir errores de validación para depuración
            print("DEBUG: Formulario inválido después de completar campos")
            for field, errors in form.errors.items():
                print(f"DEBUG: Campo {field} - Errores: {errors}")
            return self.form_invalid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['proyecto'] = get_object_or_404(Proyecto, id=self.kwargs['proyecto_id'])
        kwargs['usuario'] = self.request.user
        return kwargs

    def form_valid(self, form):
        print("DEBUG: Formulario válido. Guardando observación SSOMA...")
        form.instance.creado_por = self.request.user
        form.instance.estado = 'Pendiente'
        form.instance.proyecto = get_object_or_404(Proyecto, id=self.kwargs['proyecto_id'])
        
        # Asegurar que todos los campos requeridos tengan valores
        if not form.instance.item:
            # Generar automáticamente el número de ítem
            ultimo_item = ObservacionSeguridadSSOMA.objects.filter(proyecto=form.instance.proyecto).order_by('-item').first()
            if ultimo_item:
                try:
                    # Intentar extraer el número del último ítem y aumentarlo en 1
                    ultimo_numero = int(ultimo_item.item.split('-')[-1])
                    nuevo_numero = ultimo_numero + 1
                except (ValueError, IndexError):
                    nuevo_numero = 1
            else:
                nuevo_numero = 1
            form.instance.item = f'SSO-{nuevo_numero:03d}'
        
        # Asegurar que la fecha esté establecida
        if not form.instance.fecha:
            form.instance.fecha = timezone.now().date()
        
        # Asegurar que la semana de observación esté establecida
        if not form.instance.semana_obs:
            semana = timezone.now().date().isocalendar()[1]
            form.instance.semana_obs = f'Semana {semana}'
        
        try:
            self.object = form.save()
            print("DEBUG: Observación SSOMA guardada correctamente con ID:", self.object.id)
            messages.success(self.request, 'Observación de seguridad creada correctamente.')
            return HttpResponseRedirect(self.get_success_url())
        except Exception as e:
            print("DEBUG: Error al guardar la observación SSOMA:", str(e))
            messages.error(self.request, f"Error al guardar: {str(e)}")
            return self.form_invalid(form)

    def form_invalid(self, form):
        print("DEBUG: Formulario inválido. Errores:", form.errors)
        for field, errors in form.errors.items():
            print(f"DEBUG: Campo {field} - Errores: {errors}")
        messages.error(self.request, "El formulario contiene errores. Por favor, revisa los campos resaltados.")
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('obervaciones:lista_observaciones_ssoma', kwargs={'proyecto_id': self.kwargs['proyecto_id']})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['proyecto'] = get_object_or_404(Proyecto, id=self.kwargs['proyecto_id'])
        context['titulo'] = 'Nueva Observación de Seguridad'
        context['es_ssoma'] = True
        return context

    def get_proyecto(self):
        """Devuelve la instancia de Proyecto asociada usando los kwargs de la URL."""
        # Intenta obtener el parámetro pk o proyecto_id de la URL
        proyecto_pk = self.kwargs.get("pk") or self.kwargs.get("proyecto_id")
        return get_object_or_404(Proyecto, pk=proyecto_pk)


class DetalleObservacionSSOMAView(LoginRequiredMixin, DetailView):
    model = ObservacionSeguridadSSOMA
    template_name = 'obervaciones/detalle_observacion_ssoma.html'
    context_object_name = 'observacion'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['proyecto'] = get_object_or_404(Proyecto, id=self.kwargs['proyecto_id'])
        context['titulo'] = f'Observación de Seguridad SSOMA - {self.object.item}'
        context['es_ssoma'] = True
        context['es_editor'] = es_administrador(self.request.user) or self.request.user.is_superuser
        context['es_visor'] = not context['es_editor']
        
        # Verificar si existe un levantamiento para esta observación
        try:
            levantamiento = LevantamientoSSOMA.objects.get(observacion=self.object)
            context['tiene_levantamiento'] = True
            context['levantamiento'] = levantamiento
        except LevantamientoSSOMA.DoesNotExist:
            context['tiene_levantamiento'] = False
        
        return context


class EditarObservacionSSOMAView(LoginRequiredMixin, UpdateView):
    model = ObservacionSeguridadSSOMA
    form_class = ObservacionSeguridadSSOMAForm
    template_name = 'obervaciones/observacion_ssoma_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_superuser or es_administrador(request.user) or es_supervisor(request.user) or request.user.groups.filter(name='visores').exists()):
            messages.error(request, 'No tiene permisos para editar observaciones de seguridad.')
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['proyecto'] = get_object_or_404(Proyecto, id=self.kwargs['proyecto_id'])
        kwargs['usuario'] = self.request.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['proyecto'] = get_object_or_404(Proyecto, id=self.kwargs['proyecto_id'])
        context['titulo'] = f'Editar Observación de Seguridad SSOMA - {self.object.item}'
        context['es_ssoma'] = True
        return context
    
    def form_valid(self, form):
        try:
            self.object = form.save()
            messages.success(self.request, 'Observación de seguridad actualizada correctamente.')
            return HttpResponseRedirect(self.get_success_url())
        except Exception as e:
            print(f"ERROR: {str(e)}")
            messages.error(self.request, f"Error al actualizar: {str(e)}")
            return self.form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy('obervaciones:ver_observacion_ssoma', kwargs={'proyecto_id': self.kwargs['proyecto_id'], 'pk': self.object.pk})


class EliminarObservacionSSOMAView(LoginRequiredMixin, DeleteView):
    model = ObservacionSeguridadSSOMA
    template_name = 'obervaciones/confirmar_eliminar_observacion_ssoma.html'
    context_object_name = 'observacion'
    
    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_superuser or es_administrador(request.user)):
            messages.error(request, 'No tiene permisos para eliminar observaciones de seguridad.')
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['proyecto'] = get_object_or_404(Proyecto, id=self.kwargs['proyecto_id'])
        context['titulo'] = f'Eliminar Observación de Seguridad SSOMA - {self.object.item}'
        context['es_ssoma'] = True
        return context
    
    def delete(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
            proyecto_id = self.kwargs['proyecto_id']
            self.object.delete()
            messages.success(request, 'Observación de seguridad eliminada correctamente.')
            return HttpResponseRedirect(self.get_success_url())
        except Exception as e:
            messages.error(request, f"Error al eliminar: {str(e)}")
            return HttpResponseRedirect(self.request.path)
    
    def get_success_url(self):
        return reverse_lazy('obervaciones:lista_observaciones_ssoma', kwargs={'proyecto_id': self.kwargs['proyecto_id']})


class CrearLevantamientoSSOMAView(LoginRequiredMixin, CreateView):
    """VISOR crea el levantamiento de una observación SSOMA."""

    model = LevantamientoSSOMA
    form_class = LevantamientoSSOMAForm
    template_name = "obervaciones/levantamiento_form.html"

    def dispatch(self, request, *args, **kwargs):
        # Solo visores (no editores/superuser) pueden crear levantamientos
        if request.user.is_superuser or es_administrador(request.user):
            messages.error(request, "Los editores no pueden crear levantamientos.")
            return self.handle_no_permission()
        
        # Verificar si ya existe un levantamiento para esta observación
        observacion = self.get_observacion()
        try:
            levantamiento = LevantamientoSSOMA.objects.get(observacion=observacion)
            # Permitir crear un nuevo levantamiento si el anterior fue rechazado
            if levantamiento.estado == 'Rechazado':
                # Eliminar el levantamiento rechazado para permitir crear uno nuevo
                levantamiento.delete()
                messages.info(
                    request,
                    "El levantamiento anterior fue rechazado. Puede crear uno nuevo."
                )
            else:
                messages.warning(
                    request, 
                    f"Ya existe un levantamiento para esta observación con estado: {levantamiento.get_estado_display()}. "
                    f"No se puede crear otro levantamiento."
                )
                # Redirigir a la página de detalle de la observación
                return HttpResponseRedirect(reverse_lazy(
                    "obervaciones:ver_observacion_ssoma",
                    kwargs={
                        "proyecto_id": self.kwargs["proyecto_id"],
                        "pk": self.kwargs["observacion_id"],
                    },
                ))
        except LevantamientoSSOMA.DoesNotExist:
            # No existe levantamiento, continuar con la creación
            pass
            
        return super().dispatch(request, *args, **kwargs)

    def get_observacion(self):
        return get_object_or_404(
            ObservacionSeguridadSSOMA,
            pk=self.kwargs["observacion_id"],
            proyecto__id=self.kwargs["proyecto_id"],
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        observacion = self.get_observacion()
        context["proyecto"] = observacion.proyecto
        context["observacion"] = observacion
        context["es_ssoma"] = True
        context["titulo"] = f"Levantar Observación SSOMA {observacion.item}"
        return context

    def form_valid(self, form):
        obs = self.get_observacion()
        form.instance.observacion = obs

        # Calcular tiempo de levantamiento automáticamente
        if form.instance.fecha_levantamiento and obs.fecha:
            diff = form.instance.fecha_levantamiento - obs.fecha
            form.instance.tiempo_levantamiento = diff
        return super().form_valid(form)

    def get_success_url(self):
        messages.success(self.request, "Levantamiento enviado y pendiente de revisión.")
        return reverse_lazy(
            "obervaciones:ver_observacion_ssoma",
            kwargs={
                "proyecto_id": self.kwargs["proyecto_id"],
                "pk": self.kwargs["observacion_id"],
            },
        )


class RevisarLevantamientoSSOMAView(LoginRequiredMixin, UpdateView):
    """EDITOR revisa (aprueba/rechaza) un levantamiento SSOMA."""

    model = LevantamientoSSOMA
    template_name = "obervaciones/revisar_levantamiento.html"
    pk_url_kwarg = "levantamiento_id"
    fields = ["estado", "comentario_revisor"]

    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_superuser or es_administrador(request.user)):
            messages.error(request, "Solo editores pueden revisar levantamientos.")
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["proyecto"] = self.object.observacion.proyecto
        context["observacion"] = self.object.observacion
        context["es_ssoma"] = True
        context["es_editor"] = True  # Siempre es True porque solo los editores pueden acceder a esta vista
        context["titulo"] = f"Revisar Levantamiento SSOMA {self.object.observacion.item}"
        return context

    def form_valid(self, form):
        # Establecer el revisor y la fecha de revisión
        form.instance.revisor = self.request.user
        form.instance.revisado_en = timezone.now()
        
        # Guardar el levantamiento
        self.object = form.save()
        
        # Actualizar el estado de la observación según el estado del levantamiento
        observacion = self.object.observacion
        
        # Actualizar el estado de la observación según el estado del levantamiento
        if self.object.estado == 'Aprobado':
            # Actualizar directamente en la base de datos para evitar problemas de caché
            ObservacionSeguridadSSOMA.objects.filter(id=observacion.id).update(estado='Atendido')
            messages.success(self.request, f"Levantamiento aprobado. La observación {observacion.item} ha sido marcada como atendida.")
        elif self.object.estado == 'Rechazado':
            ObservacionSeguridadSSOMA.objects.filter(id=observacion.id).update(estado='Pendiente')
            messages.warning(self.request, f"Levantamiento rechazado. La observación {observacion.item} sigue pendiente.")
        
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy(
            "obervaciones:ver_observacion_ssoma",
            kwargs={
                "proyecto_id": self.object.observacion.proyecto.id,
                "pk": self.object.observacion.id,
            },
        )


@login_required
def observacion_ssoma_pdf(request, proyecto_id, observacion_id):
    """Genera un PDF para una observación SSOMA."""
    # Obtener la observación o retornar 404 si no existe
    observacion = get_object_or_404(
        ObservacionSeguridadSSOMA, 
        id=observacion_id, 
        proyecto__id=proyecto_id
    )
    
    try:
        # Crear el generador de PDF
        pdf_generator = ObservacionPDFGenerator()
        
        # Generar el PDF
        pdf_content = pdf_generator.generate_pdf_ssoma(observacion)
        
        # Configurar la respuesta HTTP con el PDF
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="observacion_ssoma_{observacion.id}.pdf"'
        return response
        
    except Exception as e:
        # En caso de error, registrar el error y mostrar mensaje al usuario
        import traceback
        error_msg = f'Error al generar el PDF: {str(e)}'
        print(error_msg)
        traceback.print_exc()
        messages.error(request, error_msg)
        # Redirigir a la página de detalle de la observación
        return redirect('obervaciones:ver_observacion_ssoma', proyecto_id=proyecto_id, pk=observacion_id)
