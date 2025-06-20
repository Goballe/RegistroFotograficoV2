from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView
from . import views, views_graficos
from . import views_notificaciones  # Importación separada para evitar problemas

app_name = 'reportes'

urlpatterns = [
    # URLs de autenticación
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='reportes:login'), name='logout'),
    path('registro/', views.registro_usuario, name='registro_usuario'),
    path('perfil/', views.perfil_usuario, name='perfil'),
    path('cambiar-contrasena/', views.cambiar_contrasena, name='cambiar_contrasena'),
    
    # URLs de observaciones
    path('observaciones/', include('obervaciones.urls')),
    
    # Dashboard y proyectos
    path('dashboard/', views.dashboard, name='dashboard'),
    path('proyectos/', views.listar_proyectos, name='listar_proyectos'),
    path('proyecto/crear/', views.crear_proyecto, name='crear_proyecto'),
    path('proyecto/editar/<int:proyecto_id>/', views.editar_proyecto, name='editar_proyecto'),
    path('proyecto/eliminar/<int:proyecto_id>/', views.eliminar_proyecto, name='eliminar_proyecto'),
    path('proyecto/<int:proyecto_id>/', views.proyecto_detalle, name='proyecto_detalle'),
    
    # APIs
    path('api/reportes_por_tipo/', views.api_reportes_por_tipo, name='api_reportes_por_tipo'),
    
    # Gráficos y estadísticas
    path('dashboard/graficos/', views_graficos.dashboard_graficos, name='dashboard_graficos'),
    path('api/datos_graficos/', views_graficos.api_datos_graficos, name='api_datos_graficos'),
    
    # Notificaciones
    path('api/notificaciones/', views_notificaciones.obtener_notificaciones, name='obtener_notificaciones'),
    path('api/notificaciones/marcar-leida/<int:notificacion_id>/', views_notificaciones.marcar_como_leida, name='marcar_notificacion_leida'),
    path('api/notificaciones/marcar-todas-leidas/', views_notificaciones.marcar_todas_como_leidas, name='marcar_todas_notificaciones_leidas'),
    path('notificaciones/', views_notificaciones.todas_las_notificaciones, name='todas_notificaciones'),
]
