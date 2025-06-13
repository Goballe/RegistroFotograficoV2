from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'reportes'

urlpatterns = [
    # URLs de autenticación
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='reportes:login'), name='logout'),
    path('registro/', views.registro_usuario, name='registro_usuario'),
    path('perfil/', views.perfil_usuario, name='perfil_usuario'),
    path('cambiar-contrasena/', views.cambiar_contrasena, name='cambiar_contrasena'),
    
    # Dashboard y proyectos
    path('dashboard/', views.dashboard, name='dashboard'),
    path('proyectos/', views.listar_proyectos, name='listar_proyectos'),
    path('proyecto/crear/', views.crear_proyecto, name='crear_proyecto'),
    path('proyecto/editar/<int:proyecto_id>/', views.editar_proyecto, name='editar_proyecto'),
    path('proyecto/eliminar/<int:proyecto_id>/', views.eliminar_proyecto, name='eliminar_proyecto'),
    path('proyecto/<int:proyecto_id>/', views.proyecto_detalle, name='proyecto_detalle'),
    
    # Reportes
    path('reporte/crear/', views.crear_reporte, name='crear_reporte'),
    path('reporte/editar/<int:reporte_id>/', views.editar_reporte, name='editar_reporte'),
    path('reporte/editar_reporte/<int:reporte_id>/', views.editar_reporte, name='editar_reporte_alt'),
    path('borrar/<int:reporte_id>/', views.borrar_reporte, name='borrar_reporte'),
    path('reporte/pdf/<int:reporte_id>/', views.reporte_pdf, name='reporte_pdf'),
    
    # APIs
    path('api/reportes_por_tipo/', views.api_reportes_por_tipo, name='api_reportes_por_tipo'),
]
