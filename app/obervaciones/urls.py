from django.urls import path, include
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from . import views
from . import views_ssoma
from .views_excel import ExportObservacionesCalidadExcelView, ExportObservacionesSSOMAExcelView

app_name = 'obervaciones'

# URLs para la API (si aún se necesitan)
urlpatterns_api = [
    path('get_random_table/', csrf_exempt(views.GetRandomTableView.as_view()), name='get_random_table'),
]

# URLs para la gestión de observaciones de calidad
urlpatterns_observaciones = [
    # Lista de observaciones de calidad
    path('proyecto/<int:proyecto_id>/observaciones/', 
         views.ListaObservacionesCalidadView.as_view(), 
         name='lista_observaciones'),
         
    # Las rutas de observaciones SSOMA han sido eliminadas ya que se manejarán a través del formulario de proyectos
    # Crear  para una observación

    
    # Crear nueva observación
    path('proyecto/<int:proyecto_id>/observaciones/nueva/', 
         views.CrearObservacionCalidadView.as_view(), 
         name='crear_observacion'),
    
    # Ver detalle de observación
    path('proyecto/<int:proyecto_id>/observaciones/ver/<int:observacion_id>/', 
         views.DetalleObservacionCalidadView.as_view(), 
         name='ver_observacion'),
    
    # Editar observación existente
    path('proyecto/<int:proyecto_id>/observaciones/editar/<int:observacion_id>/', 
         views.EditarObservacionCalidadView.as_view(), 
         name='editar_observacion'),
    
    # Eliminar observación
    path('proyecto/<int:proyecto_id>/observaciones/eliminar/<int:observacion_id>/', 
         views.EliminarObservacionCalidadView.as_view(), 
         name='eliminar_observacion'),
    
    # Crear levantamiento de observación (visor)
    path('proyecto/<int:proyecto_id>/observaciones/levantamiento/<int:observacion_id>/',
         views.CrearLevantamientoCalidadView.as_view(),
         name='crear_levantamiento_calidad'),
    
    # Revisar levantamiento (editor)
    path('proyecto/<int:proyecto_id>/levantamientos/<int:levantamiento_id>/revisar/',
         views.RevisarLevantamientoCalidadView.as_view(),
         name='revisar_levantamiento_calidad'),
]

# URLs para la gestión de observaciones de seguridad SSOMA
urlpatterns_ssoma = [
    # Formularios de prueba
    path('test-form/', 
         TemplateView.as_view(template_name='obervaciones/test_form.html'), 
         name='test_form'),
    path('simple-ssoma/', 
         TemplateView.as_view(template_name='obervaciones/ssoma_simple_form.html'), 
         name='simple_ssoma'),
         
    # Lista de observaciones SSOMA
    path('proyecto/<int:proyecto_id>/observaciones/ssoma/', 
         views_ssoma.ListaObservacionesSSOMAView.as_view(), 
         name='lista_observaciones_ssoma'),
         
    # Crear nueva observación SSOMA
    path('proyecto/<int:proyecto_id>/observaciones/ssoma/nueva/', 
         views_ssoma.CrearObservacionSSOMAView.as_view(), 
         name='crear_observacion_ssoma'),
    
    # Ver detalle de observación SSOMA
    path('proyecto/<int:proyecto_id>/observaciones/ssoma/ver/<int:pk>/', 
         views_ssoma.DetalleObservacionSSOMAView.as_view(), 
         name='ver_observacion_ssoma'),
    
    # Editar observación SSOMA existente
    path('proyecto/<int:proyecto_id>/observaciones/ssoma/editar/<int:pk>/', 
         views_ssoma.EditarObservacionSSOMAView.as_view(), 
         name='editar_observacion_ssoma'),
    
    # Levantamiento de observación SSOMA (usar misma vista de edición)
    path('proyecto/<int:proyecto_id>/observaciones/ssoma/levantamiento/<int:observacion_id>/', 
         views_ssoma.CrearLevantamientoSSOMAView.as_view(), 
         name='crear_levantamiento'),
    
    # Eliminar observación SSOMA
    path('proyecto/<int:proyecto_id>/observaciones/ssoma/eliminar/<int:pk>/', 
         views_ssoma.EliminarObservacionSSOMAView.as_view(), 
         name='eliminar_observacion_ssoma'),
         
    # Revisar levantamiento SSOMA (editor)
    path('proyecto/<int:proyecto_id>/observaciones/ssoma/levantamiento/<int:levantamiento_id>/revisar/', 
         views_ssoma.RevisarLevantamientoSSOMAView.as_view(), 
         name='revisar_levantamiento_ssoma'),
]

# URLs para exportación a Excel y PDF
urlpatterns_excel = [
    # Exportar observaciones de calidad a Excel
    path('proyecto/<int:proyecto_id>/observaciones/exportar-excel/',
         ExportObservacionesCalidadExcelView.as_view(),
         name='exportar_observaciones_calidad_excel'),
         
    # Exportar observaciones SSOMA a Excel
    path('proyecto/<int:proyecto_id>/observaciones/ssoma/exportar-excel/',
         ExportObservacionesSSOMAExcelView.as_view(),
         name='exportar_observaciones_ssoma_excel'),
         
    # Generar PDF de observación de calidad
    path('proyecto/<int:proyecto_id>/observaciones/pdf/<int:observacion_id>/',
         views.generar_pdf_observacion,
         name='observacion_calidad_pdf'),
         
    # Generar PDF de observación SSOMA
    path('proyecto/<int:proyecto_id>/observaciones/ssoma/pdf/<int:observacion_id>/',
         views_ssoma.observacion_ssoma_pdf,
         name='observacion_ssoma_pdf'),
]

# URLs de la aplicación
urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('tabla-observaciones/', views.TablaObservacionesView.as_view(), name='tabla_observaciones'),
]

# Incluir todas las URLs necesarias
urlpatterns = urlpatterns_api + urlpatterns_observaciones + urlpatterns_ssoma + urlpatterns_excel
