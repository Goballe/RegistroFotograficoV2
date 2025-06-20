from django.core.files.uploadhandler import MemoryFileUploadHandler, TemporaryFileUploadHandler

class CustomMemoryFileUploadHandler(MemoryFileUploadHandler):
    """
    Manejador personalizado para subir archivos en memoria que permite archivos más grandes.
    """
    def __init__(self, *args, **kwargs):
        # Aumentar el tamaño máximo de archivos en memoria a 100MB
        self.file_size_limit = 104857600  # 100MB en bytes
        # Inicializar el atributo activated que Django espera
        self.activated = True
        super().__init__(*args, **kwargs)
        
    def handle_raw_input(self, input_data, META, content_length, boundary, encoding=None):
        # Siempre permitir archivos grandes
        return None
        
    def new_file(self, *args, **kwargs):
        # Asegurarse de que activated esté establecido antes de llamar a super().new_file()
        self.activated = True
        super().new_file(*args, **kwargs)

class CustomTemporaryFileUploadHandler(TemporaryFileUploadHandler):
    """
    Manejador personalizado para subir archivos temporales que permite archivos más grandes.
    """
    def __init__(self, *args, **kwargs):
        # Inicializar el atributo activated que Django espera
        self.activated = True
        super().__init__(*args, **kwargs)
        
    def handle_raw_input(self, input_data, META, content_length, boundary, encoding=None):
        # Siempre permitir archivos grandes
        return None
        
    def new_file(self, *args, **kwargs):
        # Asegurarse de que activated esté establecido antes de llamar a super().new_file()
        self.activated = True
        super().new_file(*args, **kwargs)
