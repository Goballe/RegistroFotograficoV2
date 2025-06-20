from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.conf import settings

def validate_file_size(value):
    """
    Validador para limitar el tamaño de archivos subidos.
    Usa el valor MAX_UPLOAD_SIZE de settings.py (50MB por defecto)
    """
    max_size = getattr(settings, 'MAX_UPLOAD_SIZE', 52428800)  # 50MB por defecto
    if value.size > max_size:
        raise ValidationError(_(f'El archivo es demasiado grande. El tamaño máximo permitido es {max_size/1024/1024:.1f} MB.'))
