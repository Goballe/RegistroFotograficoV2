from django import forms
from django.forms import inlineformset_factory, CheckboxSelectMultiple
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm, UserChangeForm
from django.contrib.auth.models import User, Group
from django.utils.translation import gettext_lazy as _
from .models import ReporteFotografico, FotoReporte, Usuario, Proyecto, TipoFormularioProyecto

class RegistroUsuarioForm(forms.ModelForm):
    nombre_completo = forms.CharField(
        label='Nombre Completo',
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingresa tu nombre completo'})
    )
    password1 = forms.CharField(label='Contraseña', widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Crea una contraseña segura'}))
    password2 = forms.CharField(label='Confirmar Contraseña', widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Repite tu contraseña'}))

    class Meta:
        model = Usuario
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de usuario'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'ejemplo@empresa.com'}),
        }

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Las contraseñas no coinciden")
        return password2

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if Usuario.objects.filter(username=username).exists():
            raise forms.ValidationError("Este nombre de usuario ya está en uso.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Usuario.objects.filter(email=email).exists():
            raise forms.ValidationError("Este correo ya está en uso.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        nombre_completo = self.cleaned_data.get('nombre_completo', '').strip()
        partes = nombre_completo.split(' ', 1)
        user.first_name = partes[0]
        user.last_name = partes[1] if len(partes) > 1 else ''
        user.set_password(self.cleaned_data["password1"])
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
    proyecto = forms.ModelChoiceField(
        queryset=ReporteFotografico._meta.get_field('proyecto').remote_field.model.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Proyecto',
    )
    tipo_formulario = forms.ChoiceField(
        choices=ReporteFotografico._meta.get_field('tipo_formulario').choices,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Tipo de formulario',
        required=True,
    )
    def __init__(self, *args, **kwargs):
        initial = kwargs.get('initial', {})
        super().__init__(*args, **kwargs)
        self.fields['proyecto'].label_from_instance = lambda obj: obj.nombre
        # Si initial tiene valores para los campos de proyecto, asígnalos si el campo está vacío
        for field in ['cliente', 'contratista', 'codigo_proyecto', 'inicio_supervision']:
            if field in initial and not self.fields[field].initial:
                self.fields[field].initial = initial[field]
    # Asegurar que version_reporte solo acepte números
    version_reporte = forms.CharField(
        label='Versión del reporte',
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'pattern': '\\d*',
            'title': 'Solo se permiten números',
            'inputmode': 'numeric'
        }),
        required=True
    )
    
    # Asegurar que reporte_numero solo acepte números
    reporte_numero = forms.IntegerField(
        label='N° de Reporte',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1',
            'step': '1',
            'title': 'Solo se permiten números enteros positivos'
        }),
        required=True
    )
    
    class Meta:
        model = ReporteFotografico
        fields = [
            'proyecto', 'tipo_formulario', 'cliente', 'contratista', 'codigo_proyecto', 'version_reporte',
            'fecha_emision', 'elaborado_por', 'revisado_por', 'inicio_supervision',
            'mes_actual_obra', 'reporte_numero', 'descripcion'
        ]
        widgets = {
            'fecha_emision': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'inicio_supervision': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'cliente': forms.TextInput(attrs={'class': 'form-control'}),
            'contratista': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo_proyecto': forms.TextInput(attrs={'class': 'form-control'}),
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
        if not (self.instance.is_superuser or self.instance.rol == Usuario.Rol.ADMIN):
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

class ProyectoForm(forms.ModelForm):
    class Meta:
        model = Proyecto
        fields = [
            'nombre', 'descripcion', 'cliente', 'contratista', 
            'codigo_proyecto', 'inicio_supervision', 'imagen', 'tipos_formulario'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'cliente': forms.TextInput(attrs={'class': 'form-control'}),
            'contratista': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo_proyecto': forms.TextInput(attrs={'class': 'form-control'}),
            'inicio_supervision': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'}
            ),
            'imagen': forms.FileInput(attrs={'class': 'form-control'}),
            'tipos_formulario': CheckboxSelectMultiple(
                attrs={'class': 'form-check-input'}
            )
        }
        help_texts = {
            'tipos_formulario': 'Selecciona los tipos de formulario permitidos para este proyecto.'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ordenar los tipos de formulario por nombre
        self.fields['tipos_formulario'].queryset = TipoFormularioProyecto.objects.all().order_by('nombre')

# Formset para las fotos
FotoFormSet = inlineformset_factory(
    ReporteFotografico, 
    FotoReporte, 
    form=FotoForm, 
    extra=1, 
    can_delete=True,
    max_num=50,  # Ahora permite hasta 50 fotos
    validate_max=True,
    fields=('imagen', 'descripcion')
)
