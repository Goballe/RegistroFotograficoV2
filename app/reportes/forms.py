from django import forms
from django.forms import inlineformset_factory
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm, UserChangeForm
from django.contrib.auth.models import User, Group
from django.utils.translation import gettext_lazy as _
from .models import ReporteFotografico, FotoReporte, Usuario

class RegistroUsuarioForm(UserCreationForm):
    nombre_completo = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingresa tu nombre completo'}),
        label='Nombre Completo'
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'ejemplo@empresa.com'}),
        label='Correo Corporativo'
    )
    username = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de usuario'}),
        label='Nombre de Usuario',
        help_text='Requerido. 150 caracteres o menos. Letras, dígitos y @/./+/-/_ solamente.'
    )
    password1 = forms.CharField(
        label='Contraseña',
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Crea una contraseña segura'}),
        help_text='''
        <ul class="mb-0 ps-3">
            <li>Tu contraseña no puede ser demasiado similar a tu otra información personal.</li>
            <li>Tu contraseña debe contener al menos 8 caracteres.</li>
            <li>Tu contraseña no puede ser una contraseña de uso común.</li>
            <li>Tu contraseña no puede ser enteramente numérica.</li>
        </ul>
        '''
    )
    password2 = forms.CharField(
        label='Confirmar Contraseña',
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Repite tu contraseña'}),
        help_text='Ingresa la misma contraseña que antes, para verificación.'
    )

    class Meta:
        model = User
        fields = ('nombre_completo', 'username', 'email', 'password1', 'password2')
        
    def save(self, commit=True):
        user = super().save(commit=False)
        # Separar el nombre completo en first_name y last_name
        nombres = self.cleaned_data['nombre_completo'].split(' ', 1)
        user.first_name = nombres[0]
        if len(nombres) > 1:
            user.last_name = nombres[1]
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

class FotoForm(forms.ModelForm):
    class Meta:
        model = FotoReporte
        fields = ['imagen', 'descripcion']
        widgets = {
            'imagen': forms.FileInput(attrs={'class': 'form-control'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Descripción de la foto'})
        }

class ReporteForm(forms.ModelForm):
    class Meta:
        model = ReporteFotografico
        fields = [
            'proyecto', 'cliente', 'contratista', 'codigo_proyecto', 'version_reporte',
            'fecha_emision', 'elaborado_por', 'revisado_por', 'inicio_supervision',
            'mes_actual_obra', 'reporte_numero', 'descripcion'
        ]
        widgets = {
            'fecha_emision': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'inicio_supervision': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'proyecto': forms.TextInput(attrs={'class': 'form-control'}),
            'cliente': forms.TextInput(attrs={'class': 'form-control'}),
            'contratista': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo_proyecto': forms.TextInput(attrs={'class': 'form-control'}),
            'version_reporte': forms.TextInput(attrs={'class': 'form-control'}),
            'elaborado_por': forms.TextInput(attrs={'class': 'form-control'}),
            'revisado_por': forms.TextInput(attrs={'class': 'form-control'}),
            'mes_actual_obra': forms.NumberInput(attrs={'class': 'form-control'}),
            'reporte_numero': forms.NumberInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class PerfilUsuarioForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['first_name', 'last_name', 'email', 'telefono', 'direccion', 'rol']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'rol': forms.Select(attrs={'class': 'form-select'}, choices=Usuario.Rol.choices)
        }
        help_texts = {
            'rol': _('Selecciona el rol que mejor describa tu función en la plataforma.')
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si el usuario no es administrador, ocultar el campo de rol
        if not (self.instance.is_superuser or self.instance.rol == Usuario.Rol.ADMINISTRADOR):
            self.fields['rol'].widget = forms.HiddenInput()

class CambiarContrasenaForm(PasswordChangeForm):
    old_password = forms.CharField(
        label=_("Contraseña actual"),
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )
    new_password1 = forms.CharField(
        label=_("Nueva contraseña"),
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text=_(
            'Tu contraseña debe contener al menos 8 caracteres y no puede ser completamente numérica.'
        ),
    )
    new_password2 = forms.CharField(
        label=_("Confirmar nueva contraseña"),
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = Usuario
        fields = ('old_password', 'new_password1', 'new_password2')

# Formset para las fotos
FotoFormSet = inlineformset_factory(
    ReporteFotografico, 
    FotoReporte, 
    form=FotoForm, 
    extra=1, 
    can_delete=True,
    max_num=10,
    validate_max=True,
    fields=('imagen', 'descripcion')
)
