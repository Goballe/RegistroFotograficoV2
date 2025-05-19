from django.db import models
from django.urls import reverse
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils.translation import gettext_lazy as _
import os

class Usuario(AbstractUser):
    class Rol(models.TextChoices):
        ADMINISTRADOR = 'ADMIN', _('Administrador')
        SUPERVISOR = 'SUPER', _('Supervisor')
        FOTOGRAFO = 'FOTO', _('Fotógrafo')
        VISOR = 'VISOR', _('Visor')
    
    rol = models.CharField(
        max_length=5,
        choices=Rol.choices,
        default=Rol.VISOR,
        verbose_name='Rol del usuario'
    )
    telefono = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    
    # Relación many-to-many para grupos y permisos personalizados
    groups = models.ManyToManyField(
        Group,
        verbose_name=_('groups'),
        blank=True,
        help_text=_('The groups this user belongs to.'),
        related_name="usuario_groups",
        related_query_name="usuario",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name="usuario_permissions",
        related_query_name="usuario",
    )
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_rol_display()})"
    
    def es_administrador(self):
        return self.rol == self.Rol.ADMINISTRADOR or self.is_superuser
    
    def puede_editar_reporte(self, reporte):
        if self.es_administrador():
            return True
        return reporte.elaborado_por == self.get_full_name()
    
    def puede_eliminar_reporte(self, reporte):
        return self.es_administrador()
    
    def puede_ver_todos_reportes(self):
        return self.rol in [self.Rol.ADMINISTRADOR, self.Rol.SUPERVISOR] or self.is_superuser
    
    def puede_crear_reporte(self):
        return self.rol in [self.Rol.ADMINISTRADOR, self.Rol.SUPERVISOR, self.Rol.FOTOGRAFO] or self.is_superuser

class ReporteFotografico(models.Model):
    proyecto = models.CharField("Proyecto", max_length=200)
    cliente = models.CharField("Cliente", max_length=200)
    contratista = models.CharField("Contratista", max_length=200)
    codigo_proyecto = models.CharField("Código del proyecto", max_length=50)
    version_reporte = models.CharField("Versión del reporte", max_length=10)
    fecha_emision = models.DateField("Fecha de emisión")
    elaborado_por = models.CharField("Elaborado por", max_length=100)
    revisado_por = models.CharField("Revisado por", max_length=100)
    inicio_supervision = models.DateField("Inicio de la Supervisión")
    mes_actual_obra = models.PositiveIntegerField("Mes Actual de Obra")
    reporte_numero = models.PositiveIntegerField("Reporte N°")
    descripcion = models.TextField("Descripción", blank=True, null=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.proyecto} - {self.fecha_emision}'

    def get_absolute_url(self):
        return reverse('reporte_pdf', args=[str(self.id)])

class FotoReporte(models.Model):
    reporte = models.ForeignKey(ReporteFotografico, related_name='fotos', on_delete=models.CASCADE)
    imagen = models.ImageField("Fotografía", upload_to='fotos/')
    orden = models.PositiveIntegerField("Orden", default=0)
    descripcion = models.CharField("Descripción", max_length=200, blank=True, null=True)
    
    class Meta:
        ordering = ['orden']
    
    def __str__(self):
        return f"Foto {self.orden} - {self.reporte.proyecto}"
        
    def delete(self, *args, **kwargs):
        # Eliminar el archivo de imagen cuando se elimina el objeto
        if os.path.isfile(self.imagen.path):
            os.remove(self.imagen.path)
        super().delete(*args, **kwargs)
