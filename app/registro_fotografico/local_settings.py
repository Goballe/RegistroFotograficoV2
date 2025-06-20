# Configuraciones locales que sobrescriben settings.py

# Aumentar el límite de tamaño de archivos a 50MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50MB en bytes
FILE_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50MB en bytes
MAX_UPLOAD_SIZE = 52428800  # 50MB en bytes

# Configuración para formularios
FORM_RENDERER = 'django.forms.renderers.TemplatesSetting'

# Asegurar que los formularios no tengan campos de solo lectura por defecto
FORM_FIELDS_READONLY = False
