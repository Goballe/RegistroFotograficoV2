from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Proyecto, ReporteFotografico, TipoFormularioProyecto, Usuario

class ProyectoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion', 'cliente', 'contratista', 'codigo_proyecto', 'inicio_supervision')
    fields = ('nombre', 'descripcion', 'cliente', 'contratista', 'codigo_proyecto', 'inicio_supervision', 'usuarios', 'tipos_formulario', 'imagen')
    filter_horizontal = ('usuarios', 'tipos_formulario')

class UsuarioAdmin(UserAdmin):
    model = Usuario
    list_display = ('username', 'email', 'first_name', 'last_name', 'rol', 'is_active', 'is_staff')
    list_filter = ('rol', 'is_active', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        ('Información adicional', {'fields': ('rol', 'telefono', 'direccion')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Información adicional', {'fields': ('rol', 'telefono', 'direccion')}),
    )
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)

class TipoFormularioProyectoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "proyectos")
    search_fields = ("nombre",)
    def proyectos(self, obj):
        return ", ".join([p.nombre for p in obj.proyecto_set.all()])
    proyectos.short_description = "Proyectos asociados"

admin.site.register(Usuario, UsuarioAdmin)
admin.site.register(TipoFormularioProyecto, TipoFormularioProyectoAdmin)
admin.site.register(Proyecto, ProyectoAdmin)
# admin.site.unregister(ReporteFotografico)  # No registrar ReporteFotografico para ocultarlo