from django.conf import settings
from django.http import HttpResponseForbidden

class FileSizeMiddleware:
    """
    Middleware para asegurar que los archivos subidos no excedan el tamaño máximo permitido
    establecido en settings.MAX_UPLOAD_SIZE
    """
    def __init__(self, get_response):
        self.get_response = get_response
        # Configuración de tamaño máximo (100MB por defecto)
        self.max_upload_size = getattr(settings, 'MAX_UPLOAD_SIZE', 104857600)

    def __call__(self, request):
        if request.method == 'POST' and request.FILES:
            for uploaded_file in request.FILES.values():
                if uploaded_file.size > self.max_upload_size:
                    return HttpResponseForbidden(
                        f"El archivo subido es demasiado grande. "
                        f"El tamaño máximo permitido es {self.max_upload_size/1024/1024:.1f} MB."
                    )
        return self.get_response(request)
