from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from .models import ObservacionCalidad, ObservacionSeguridadSSOMA, TipoObservacionSSOMA, AreaSSOMA, SubClasificacion
from django.forms import TextInput, Textarea, Select, DateInput, FileInput, ModelChoiceField
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
            
            # Ya no establecemos valor predeterminado para semana_obs, lo dejamos en blanco para que el usuario lo llene
            
        # Filtrar el campo asignado_a para mostrar solo usuarios del grupo 'visores'
        self.fields['asignado_a'].queryset = User.objects.filter(
            groups__name='visores', is_active=True
        ).order_by('first_name', 'last_name')


class ObservacionSeguridadSSOMAForm(forms.ModelForm):
    """Formulario para crear y editar observaciones de seguridad SSOMA."""
    
    class Meta:
        model = ObservacionSeguridadSSOMA
        fields = [
            'item', 'tipo_observacion', 'area', 'semana_obs', 'fecha',
            'punto_inspeccion', 'subclasificacion', 'descripcion', 'accion_correctiva', 'nivel_riesgo',
            'estado', 'foto_1', 'foto_2', 'asignado_a'
        ]
        widgets = {
            'fecha': DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'item': TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'semana_obs': TextInput(attrs={'class': 'form-control'}),
            'tipo_observacion': Select(attrs={'class': 'form-select'}),
            'area': Select(attrs={'class': 'form-select'}),
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
            
            # Ya no establecemos valor predeterminado para semana_obs, lo dejamos en blanco para que el usuario lo llene
            
        # Filtrar el campo asignado_a para mostrar solo usuarios del grupo 'visores'
        self.fields['asignado_a'].queryset = User.objects.filter(
            groups__name='visores', is_active=True
        ).order_by('first_name', 'last_name')
