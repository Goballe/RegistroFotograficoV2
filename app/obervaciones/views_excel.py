from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404
from django.views import View

from reportes.models import Proyecto
from .models import ObservacionCalidad, ObservacionSeguridadSSOMA
from .utils import export_observaciones_calidad_to_excel, export_observaciones_ssoma_to_excel
from .views import es_visor, es_editor


class ExportObservacionesCalidadExcelView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Vista para exportar observaciones de calidad a Excel."""
    
    def test_func(self):
        return es_visor(self.request.user) or es_editor(self.request.user)
    
    def get(self, request, proyecto_id):
        proyecto = get_object_or_404(Proyecto, pk=proyecto_id)
        observaciones = ObservacionCalidad.objects.filter(proyecto=proyecto).order_by('item')
        return export_observaciones_calidad_to_excel(observaciones)


class ExportObservacionesSSOMAExcelView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Vista para exportar observaciones de SSOMA a Excel."""
    
    def test_func(self):
        return es_visor(self.request.user) or es_editor(self.request.user)
    
    def get(self, request, proyecto_id):
        proyecto = get_object_or_404(Proyecto, pk=proyecto_id)
        observaciones = ObservacionSeguridadSSOMA.objects.filter(proyecto=proyecto).order_by('item')
        return export_observaciones_ssoma_to_excel(observaciones)
