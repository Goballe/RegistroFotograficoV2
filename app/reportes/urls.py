from django.urls import path
from . import views

urlpatterns = [
    path('borrar/<int:reporte_id>/', views.borrar_reporte, name='borrar_reporte'),
    path('crear/', views.crear_reporte, name='crear_reporte'),
    path('', views.lista_reportes, name='lista_reportes'),
    path('pdf/<int:reporte_id>/', views.reporte_pdf, name='reporte_pdf'),
]
