from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from .models import ObservacionCalidad, ObservacionSeguridadSSOMA, TipoObservacionSSOMA, AreaSSOMA, SubClasificacion, LevantamientoSSOMA
from reportes.models import Proyecto
from django.forms import ModelForm, TextInput, Select, Textarea, DateInput, FileInput, CheckboxInput, HiddenInput, ModelChoiceField
from datetime import datetime

User = get_user_model()

class ObservacionCalidadForm(forms.ModelForm):
    """Formulario para crear y editar observaciones de calidad."""
    
    class Meta:
        model = ObservacionCalidad
        fields = [
            'item', 'semana_obs', 'fecha', 'punto_inspeccion', 'sub_clasificacion', 'descripcion',
            'recomendacion', 'nivel_riesgo', 'estado', 'foto_1', 'foto_2', 'asignado_a'
        ]
        widgets = {
            'fecha': DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'descripcion': Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'recomendacion': Textarea(attrs={'rows': 3, 'class': 'form-control'}),

            'item': TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'semana_obs': TextInput(attrs={'class': 'form-control'}),
            'punto_inspeccion': Select(attrs={'class': 'form-select'}),
            'sub_clasificacion': Select(attrs={'class': 'form-select'}),
            'nivel_riesgo': Select(attrs={'class': 'form-select'}),
            'estado': Select(attrs={'class': 'form-select'}),
            'asignado_a': Select(attrs={'class': 'form-select'}),
            'foto_1': FileInput(attrs={'class': 'form-control'}),
            'foto_2': FileInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        # Extraer proyecto y usuario si están presentes
        self.proyecto = kwargs.pop('proyecto', None)
        self.usuario = kwargs.pop('usuario', None)
        
        super().__init__(*args, **kwargs)
        
        # Si hay un proyecto, asignarlo a la instancia
        if self.proyecto and not self.instance.pk:
            self.instance.proyecto = self.proyecto
            
            # Generar automáticamente el número de ítem
            ultimo_item = ObservacionCalidad.objects.filter(proyecto=self.proyecto).order_by('-item').first()
            if ultimo_item:
                try:
                    # Intentar extraer el número del último ítem y aumentarlo en 1
                    ultimo_numero = int(ultimo_item.item.split('-')[-1])
                    nuevo_numero = ultimo_numero + 1
                except (ValueError, IndexError):
                    # Si no se puede extraer un número, empezar desde 1
                    nuevo_numero = 1
            else:
                # Si no hay ítems previos, empezar desde 1
                nuevo_numero = 1
                
            # Formatear el nuevo ítem como 'CAL-001', 'CAL-002', etc.
            nuevo_item = f'CAL-{nuevo_numero:03d}'
            
            # Establecer el valor inicial del campo item
            self.fields['item'].initial = nuevo_item
            self.instance.item = nuevo_item
            
            # Calcular automáticamente la semana de observación
            from datetime import datetime
            from math import ceil
            
            fecha_actual = datetime.now().date()
            
            # Verificar si el proyecto tiene fecha de inicio de supervisión
            if self.proyecto.inicio_supervision:
                # Calcular la diferencia en días
                delta_dias = (fecha_actual - self.proyecto.inicio_supervision).days
                # Calcular la diferencia en semanas (redondeando hacia arriba)
                semanas = ceil(delta_dias / 7)
                self.fields['semana_obs'].initial = f'Semana {semanas}'
                self.instance.semana_obs = f'Semana {semanas}'
            else:
                # Si no hay fecha de inicio, usar la semana del año actual
                semana_actual = fecha_actual.isocalendar()[1]
                self.fields['semana_obs'].initial = f'Semana {semana_actual}'
                self.instance.semana_obs = f'Semana {semana_actual}'
            
        # Filtrar el campo asignado_a para mostrar solo usuarios del grupo 'visores'
        self.fields['asignado_a'].queryset = User.objects.filter(
            groups__name='visores', is_active=True
        ).order_by('first_name', 'last_name')


class ObservacionSeguridadSSOMAForm(forms.ModelForm):
    """Formulario para crear y editar observaciones de seguridad SSOMA."""
    
    class Meta:
        model = ObservacionSeguridadSSOMA
        fields = [
            'item', 'tipo_observacion', 'semana_obs', 'fecha',
            'punto_inspeccion', 'subclasificacion', 'descripcion', 'accion_correctiva', 'nivel_riesgo',
            'estado', 'foto_1', 'foto_2', 'asignado_a'
        ]
        widgets = {
            'fecha': DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'item': TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'semana_obs': TextInput(attrs={'class': 'form-control'}),
            'tipo_observacion': Select(attrs={'class': 'form-select'}),
            'punto_inspeccion': Select(attrs={'class': 'form-select'}),
            'subclasificacion': Select(attrs={'class': 'form-select'}),
            'descripcion': Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'accion_correctiva': Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'nivel_riesgo': Select(attrs={'class': 'form-select'}),
            'estado': Select(attrs={'class': 'form-select'}),
            'asignado_a': Select(attrs={'class': 'form-select'}),
            'foto_1': FileInput(attrs={'class': 'form-control'}),
            'foto_2': FileInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        # Extraer proyecto y usuario si están presentes
        self.proyecto = kwargs.pop('proyecto', None)
        self.usuario = kwargs.pop('usuario', None)
        
        super().__init__(*args, **kwargs)
        
        # Establecer etiquetas personalizadas para los campos
        self.fields['descripcion'].label = 'Descripción de la Observación'
        self.fields['accion_correctiva'].label = 'Acción Correctiva'
        self.fields['subclasificacion'].label = 'Subclasificación'
        
        # Si hay un proyecto, asignarlo a la instancia
        if self.proyecto and not self.instance.pk:
            self.instance.proyecto = self.proyecto
            
            # Generar automáticamente el número de ítem
            ultimo_item = ObservacionSeguridadSSOMA.objects.filter(proyecto=self.proyecto).order_by('-item').first()
            if ultimo_item:
                try:
                    # Intentar extraer el número del último ítem y aumentarlo en 1
                    ultimo_numero = int(ultimo_item.item.split('-')[-1])
                    nuevo_numero = ultimo_numero + 1
                except (ValueError, IndexError):
                    # Si no se puede extraer un número, empezar desde 1
                    nuevo_numero = 1
            else:
                # Si no hay ítems previos, empezar desde 1
                nuevo_numero = 1
                
            # Formatear el nuevo ítem como 'SSO-001', 'SSO-002', etc.
            nuevo_item = f'SSO-{nuevo_numero:03d}'
            
            # Establecer el valor inicial del campo item
            self.fields['item'].initial = nuevo_item
            self.instance.item = nuevo_item
            
            # Establecer valores predeterminados para campos requeridos
            from django.utils import timezone
            from datetime import datetime
            from math import ceil
            
            # Fecha actual como valor predeterminado
            fecha_actual = timezone.now().date()
            self.fields['fecha'].initial = fecha_actual
            
            # Calcular automáticamente la semana de observación
            if self.proyecto.inicio_supervision:
                # Calcular la diferencia en días
                delta_dias = (fecha_actual - self.proyecto.inicio_supervision).days
                # Calcular la diferencia en semanas (redondeando hacia arriba)
                semanas = ceil(delta_dias / 7)
                self.fields['semana_obs'].initial = f'Semana {semanas}'
                self.instance.semana_obs = f'Semana {semanas}'
            else:
                # Si no hay fecha de inicio, usar la semana del año actual
                semana_actual = fecha_actual.isocalendar()[1]
                self.fields['semana_obs'].initial = f'Semana {semana_actual}'
                self.instance.semana_obs = f'Semana {semana_actual}'
            
            # Valores predeterminados para campos de selección
            self.fields['tipo_observacion'].initial = 'Acto Inseguro'
            self.fields['nivel_riesgo'].initial = 'Medio'
            self.fields['estado'].initial = 'Pendiente'
            
        # Remover completamente el campo área si existe
        self.fields.pop('area', None)
        
        # Filtrar el campo asignado_a para mostrar solo usuarios del grupo 'visores'
        self.fields['asignado_a'].queryset = User.objects.filter(
            groups__name='visores', is_active=True
        ).order_by('first_name', 'last_name')


# -------------------- Formularios de levantamiento -------------------------

class LevantamientoSSOMAForm(forms.ModelForm):
    """Formulario para que los VISOR llenen el levantamiento de una observación SSOMA."""

    class Meta:
        from .models import LevantamientoSSOMA  # import local para evitar errores circulares
        model = LevantamientoSSOMA
        fields = [
            "semana_levantamiento",
            "fecha_levantamiento",
            "descripcion",
            "fotografia",
            "tiempo_levantamiento",
        ]

        widgets = {
            "semana_levantamiento": TextInput(attrs={"class": "form-control"}),
            "fecha_levantamiento": DateInput(attrs={"type": "date", "class": "form-control"}),
            "descripcion": Textarea(attrs={"rows": 3, "class": "form-control"}),
            "fotografia": FileInput(attrs={"class": "form-control"}),
            "tiempo_levantamiento": TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "hh:mm:ss",
                    "readonly": "readonly",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # El campo se llenará automáticamente; no debe ser requerido ni editable
        t = self.fields.get("tiempo_levantamiento")
        if t:
            t.required = False
            t.help_text = "Se calcula automáticamente"
            t.disabled = True


class LevantamientoCalidadForm(forms.ModelForm):
    """Formulario para que los VISOR llenen el levantamiento de una observación de calidad."""

    class Meta:
        from .models import LevantamientoObservacion  # import local para evitar errores si no existe

        model = LevantamientoObservacion
        fields = [
            "semana_levantamiento",
            "fecha_levantamiento",
            "descripcion",
            "fotografia",
            "tiempo_levantamiento",
        ]

        widgets = {
            "semana_levantamiento": TextInput(attrs={"class": "form-control"}),
            "fecha_levantamiento": DateInput(attrs={"type": "date", "class": "form-control"}),
            "descripcion": Textarea(attrs={"rows": 3, "class": "form-control"}),
            "fotografia": FileInput(attrs={"class": "form-control"}),
            "tiempo_levantamiento": TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "hh:mm:ss",
                    "readonly": "readonly",
                }
            ),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # El campo se llenará automáticamente; no debe ser requerido ni editable
        t = self.fields.get("tiempo_levantamiento")
        if t:
            t.required = False
            t.help_text = "Se calcula automáticamente"
            t.disabled = True
