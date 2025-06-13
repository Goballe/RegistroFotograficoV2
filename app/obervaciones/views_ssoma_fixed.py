from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from .models import ObservacionSeguridadSSOMA
from .forms import ObservacionSeguridadSSOMAForm
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
        # Permitir solo a superuser, admin o supervisor
        if not (request.user.is_superuser or es_administrador(request.user) or es_supervisor(request.user)):
            messages.error(request, 'No tiene permisos para crear observaciones de seguridad.')
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['proyecto'] = get_object_or_404(Proyecto, id=self.kwargs['proyecto_id'])
        kwargs['usuario'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.creado_por = self.request.user
        form.instance.estado = 'Pendiente'
        response = super().form_valid(form)
        messages.success(self.request, 'Observación de seguridad creada correctamente.')
        return response

    def form_invalid(self, form):
        print("DEBUG: Formulario inválido. Errores:", form.errors)
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
