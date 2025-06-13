"""
Prueba para verificar el registro del modelo en el admin.
"""
from django.test import TestCase
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.urls import reverse

from obervaciones.admin import ObservacionSeguridadSSOMAAdmin
from obervaciones.models import ObservacionSeguridadSSOMA
from reportes.models import Proyecto


class MockRequest:
    pass


class TestObservacionSeguridadSSOMAAdmin(TestCase):
    """Pruebas para el admin de ObservacionSeguridadSSOMA."""

    @classmethod
    def setUpTestData(cls):
        """Configuración inicial para las pruebas."""
        # Crear un superusuario
        User = get_user_model()
        cls.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123',
            is_staff=True
        )
        
        # Crear un proyecto de prueba
        cls.proyecto = Proyecto.objects.create(
            codigo_proyecto='TEST001',
            nombre='Proyecto de Prueba',
            descripcion='Proyecto para pruebas',
            cliente='Cliente de Prueba',
            contratista='Contratista de Prueba'
        )
        
        # Crear una observación de prueba
        cls.observacion = ObservacionSeguridadSSOMA.objects.create(
            proyecto=cls.proyecto,
            item='TEST-001',
            tipo_observacion='Condición Insegura',
            area='Obra Civil',
            semana_obs='2023-01',
            fecha='2023-01-15',
            descripcion='Descripción de prueba',
            accion_correctiva='Acción correctiva de prueba',
            nivel_riesgo='Alto',
            estado='Pendiente',
            creado_por=cls.superuser
        )
    
    def test_admin_list_display(self):
        """Verificar que los campos de list_display estén configurados correctamente."""
        admin = ObservacionSeguridadSSOMAAdmin(ObservacionSeguridadSSOMA, None)
        self.assertEqual(
            admin.list_display,
            ('item', 'tipo_observacion', 'area', 'fecha', 'nivel_riesgo_badge', 'estado_badge', 'asignado_a')
        )
    
    def test_admin_search_fields(self):
        """Verificar que los campos de búsqueda estén configurados correctamente."""
        admin = ObservacionSeguridadSSOMAAdmin(ObservacionSeguridadSSOMA, None)
        self.assertEqual(
            admin.search_fields,
            ('item', 'descripcion', 'accion_correctiva')
        )
    
    def test_admin_list_filter(self):
        """Verificar que los filtros estén configurados correctamente."""
        admin = ObservacionSeguridadSSOMAAdmin(ObservacionSeguridadSSOMA, None)
        self.assertEqual(
            admin.list_filter,
            ('tipo_observacion', 'area', 'nivel_riesgo', 'estado', 'asignado_a')
        )
    
    def test_admin_has_add_permission(self):
        """Verificar que el admin tenga permiso para agregar."""
        request = RequestFactory().get(reverse('admin:obervaciones_observacionseguridadssoma_add'))
        request.user = self.superuser
        admin = ObservacionSeguridadSSOMAAdmin(ObservacionSeguridadSSOMA, None)
        self.assertTrue(admin.has_add_permission(request))
    
    def test_admin_has_change_permission(self):
        """Verificar que el admin tenga permiso para cambiar."""
        request = RequestFactory().get(reverse('admin:obervaciones_observacionseguridadssoma_change', args=[self.observacion.id]))
        request.user = self.superuser
        admin = ObservacionSeguridadSSOMAAdmin(ObservacionSeguridadSSOMA, None)
        self.assertTrue(admin.has_change_permission(request, self.observacion))
    
    def test_admin_has_delete_permission(self):
        """Verificar que el admin tenga permiso para eliminar."""
        request = RequestFactory().get(reverse('admin:obervaciones_observacionseguridadssoma_delete', args=[self.observacion.id]))
        request.user = self.superuser
        admin = ObservacionSeguridadSSOMAAdmin(ObservacionSeguridadSSOMA, None)
        self.assertTrue(admin.has_delete_permission(request, self.observacion))
