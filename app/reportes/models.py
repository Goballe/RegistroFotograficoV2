from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils.translation import gettext_lazy as _

class Usuario(AbstractUser):
    class Rol(models.TextChoices):
        ADMIN = 'ADMIN', _('Administrador')
        EDITOR = 'EDITOR', _('Editor')
        VISOR = 'VISOR', _('Visor')
    
    rol = models.CharField(
        max_length=6,
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
        return self.rol == self.Rol.ADMIN or self.is_superuser

    def puede_editar_reporte(self, reporte):
        # Solo admin y editor pueden editar
        return self.rol in [self.Rol.ADMIN, self.Rol.EDITOR] or self.is_superuser

    def puede_eliminar_reporte(self, reporte):
        # Solo admin puede eliminar
        return self.rol == self.Rol.ADMIN or self.is_superuser

    def puede_ver_todos_reportes(self):
        # Admin y editor pueden ver todos, visor solo los que le correspondan
        return self.rol in [self.Rol.ADMIN, self.Rol.EDITOR] or self.is_superuser

    def puede_crear_reporte(self):
        # Admin y editor pueden crear
        return self.rol in [self.Rol.ADMIN, self.Rol.EDITOR] or self.is_superuser

class TipoFormularioProyecto(models.Model):
    TIPO_CHOICES = [
        ('CONTROL DE OBS CALIDAD', 'CONTROL DE OBS CALIDAD'),
        ('CONTROL DE OBS SSOMA', 'OBSERVACIONES SSOMA'),
        ('CONTROL DE NC CALIDAD', 'CONTROL DE NC CALIDAD'),
        ('CONTROL DE NC SSOMA', 'CONTROL DE NC SSOMA'),
        ('CONTROL DE RFI', 'CONTROL DE RFI'),
        ('CONTROL DE ODC', 'CONTROL DE ODC'),
        ('CONTROL DE VALORIZACIONES', 'CONTROL DE VALORIZACIONES'),
        ('CONTROL DE DOSSIER', 'CONTROL DE DOSSIER'),
        ('CONTROL DE CARTAS', 'CONTROL DE CARTAS'),
    ]
    nombre = models.CharField(max_length=40, choices=TIPO_CHOICES, unique=True)

    def __str__(self):
        return self.nombre

class Proyecto(models.Model):
    nombre = models.CharField(max_length=200, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    cliente = models.CharField("Cliente", max_length=200, blank=True, null=True)
    contratista = models.CharField("Contratista", max_length=200, blank=True, null=True)
    codigo_proyecto = models.CharField("Código del proyecto", max_length=50, blank=True, null=True)
    inicio_supervision = models.DateField("Inicio de la Supervisión", blank=True, null=True)
    usuarios = models.ManyToManyField('Usuario', related_name='proyectos', verbose_name='Usuarios con acceso')
    imagen = models.ImageField("Imagen del proyecto", upload_to='proyectos/', blank=True, null=True)
    tipos_formulario = models.ManyToManyField(
        TipoFormularioProyecto,
        blank=True,
        verbose_name='Tipos de formulario disponibles',
        help_text='Selecciona los tipos de formulario permitidos para este proyecto.'
    )

    def __str__(self):
        return self.nombre
