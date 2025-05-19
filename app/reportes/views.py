from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from django.template.loader import render_to_string, get_template
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, authenticate, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from django.utils.translation import gettext_lazy as _, activate, get_language, gettext
from django.utils import translation
from django.db import transaction
from django.urls import reverse_lazy
from .models import ReporteFotografico, FotoReporte, Usuario
from .forms import ReporteForm, RegistroUsuarioForm, FotoFormSet, PerfilUsuarioForm, CambiarContrasenaForm
from xhtml2pdf import pisa
from django.template.loader import get_template
from django.template import Context
from django.http import HttpResponse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
import os
from urllib.parse import urlparse
import io
import tempfile

@login_required
def crear_reporte(request):
    if request.method == 'POST':
        form = ReporteForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                reporte = form.save(commit=False)
                reporte.save()
                
                foto_formset = FotoFormSet(request.POST, request.FILES, instance=reporte)
                if foto_formset.is_valid():
                    foto_formset.save()
                    return redirect('reporte_pdf', reporte_id=reporte.id)
                else:
                    # Si hay errores en los formularios de fotos, mostrarlos
                    messages.error(request, 'Por favor corrija los errores en las imágenes.')
        else:
            foto_formset = FotoFormSet(request.POST, request.FILES)
    else:
        form = ReporteForm()
        foto_formset = FotoFormSet(queryset=FotoReporte.objects.none())
    
    return render(request, 'reportes/crear_reporte.html', {
        'form': form,
        'foto_formset': foto_formset,
    })

def lista_reportes(request):
    reportes = ReporteFotografico.objects.prefetch_related('fotos').all().order_by('-fecha_emision')
    return render(request, 'reportes/lista_reportes.html', {'reportes': reportes})

def borrar_reporte(request, reporte_id):
    reporte = get_object_or_404(ReporteFotografico, id=reporte_id)
    reporte.delete()
    return redirect('lista_reportes')

@login_required
def perfil_usuario(request):
    if request.method == 'POST':
        form = PerfilUsuarioForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _('Tu perfil ha sido actualizado correctamente.'))
            return redirect('perfil_usuario')
    else:
        form = PerfilUsuarioForm(instance=request.user)
    
    return render(request, 'registration/perfil.html', {
        'form': form,
        'active_tab': 'perfil'
    })

@login_required
def cambiar_contrasena(request):
    if request.method == 'POST':
        form = CambiarContrasenaForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, _('Tu contraseña ha sido cambiada exitosamente.'))
            return redirect('perfil_usuario')
    else:
        form = CambiarContrasenaForm(request.user)
    
    return render(request, 'registration/cambiar_contrasena.html', {
        'form': form,
        'active_tab': 'contrasena'
    })

def registro_usuario(request):
    if request.user.is_authenticated:
        return redirect('perfil_usuario')
        
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password1'])
            user.save()
            
            # Autenticar al usuario después del registro
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, _('¡Registro exitoso! Ahora estás conectado.'))
                return redirect('lista_reportes')
    else:
        form = RegistroUsuarioForm()
    
    return render(request, 'registration/registro.html', {'form': form})

def reporte_pdf(request, reporte_id):
    reporte = get_object_or_404(ReporteFotografico, id=reporte_id)
    fotos = reporte.fotos.all()
    
    # Ruta al logo
    logo_path = os.path.join(settings.STATIC_ROOT, 'img', 'logo_jlv.jpg')
    logo_url = None
    if os.path.exists(logo_path):
        logo_url = os.path.join(settings.STATIC_URL, 'img', 'logo_jlv.jpg')
    
    # Preparar contexto con las imágenes
    with translation.override('es'):
        # Preparar rutas de las imágenes
        fotos_list = []
        for i, foto in enumerate(fotos, 1):
            if not foto.imagen:
                continue
                
            try:
                # Obtener la URL de la imagen
                foto_url = f"{request.scheme}://{request.get_host()}{foto.imagen.url}"
                relative_url = str(foto.imagen)
                
                # Para el PDF, necesitamos la ruta del sistema de archivos
                foto_path = None
                if hasattr(foto.imagen, 'path') and foto.imagen.path:
                    if os.path.exists(foto.imagen.path):
                        foto_path = foto.imagen.path
                    # Si no existe, intentar con la ruta relativa a MEDIA_ROOT
                    elif settings.MEDIA_ROOT:
                        media_relative = str(foto.imagen)
                        full_path = os.path.join(settings.MEDIA_ROOT, media_relative)
                        if os.path.exists(full_path):
                            foto_path = full_path
                
                # Si no se encontró la ruta del sistema de archivos, usar la URL
                if not foto_path or not os.path.exists(foto_path):
                    print(f"[INFO] Usando URL para la imagen {i}: {foto_url}")
                    # Para el PDF, necesitamos una ruta de archivo, no una URL
                    # Intentar descargar la imagen temporalmente
                    try:
                        import tempfile
                        import urllib.request
                        import shutil
                        
                        # Crear directorio temporal si no existe
                        temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp')
                        os.makedirs(temp_dir, exist_ok=True)
                        
                        # Descargar la imagen
                        temp_path = os.path.join(temp_dir, os.path.basename(relative_url))
                        with urllib.request.urlopen(foto_url) as response, open(temp_path, 'wb') as out_file:
                            shutil.copyfileobj(response, out_file)
                        
                        if os.path.exists(temp_path):
                            foto_path = temp_path
                            print(f"[INFO] Imagen descargada temporalmente a: {temp_path}")
                    except Exception as e:
                        print(f"[ERROR] No se pudo descargar la imagen: {str(e)}")
                        foto_path = None
                
                # Usar datos en base64 si no se pudo obtener la ruta del archivo
                if not foto_path or not os.path.exists(foto_path):
                    try:
                        import base64
                        with open(foto.imagen.path, 'rb') as img_file:
                            foto_base64 = base64.b64encode(img_file.read()).decode('utf-8')
                            foto_path = f"data:image/jpeg;base64,{foto_base64}"
                            print("[INFO] Usando datos en base64 para la imagen")
                    except Exception as e:
                        print(f"[ERROR] No se pudo codificar la imagen en base64: {str(e)}")
                        foto_path = None
                
                # Si todo falla, usar un placeholder
                if not foto_path:
                    foto_path = "data:image/svg+xml;charset=UTF-8,%3Csvg%20width%3D%22100%22%20height%3D%22100%22%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%3E%3Crect%20width%3D%22100%25%22%20height%3D%22100%25%22%20fill%3D%22%23f0f0f0%22%2F%3E%3Ctext%20x%3D%2250%25%22%20y%3D%2250%25%22%20font-family%3D%22Arial%22%20font-size%3D%2210%22%20text-anchor%3D%22middle%22%20dominant-baseline%3D%22middle%22%3EImagen%20no%20disponible%3C%2Ftext%3E%3C%2Fsvg%3E"
                    print("[WARNING] Usando placeholder para la imagen")
                
                fotos_list.append({
                    'imagen': foto,
                    'path': foto_path,            # Ruta del sistema de archivos, URL o datos en base64
                    'url': foto_url,               # URL completa para la vista previa
                    'relative_url': relative_url,  # Ruta relativa para depuración
                    'descripcion': foto.descripcion or f"Foto {i}",
                    'fecha_toma': getattr(foto.imagen, 'created', None) or "Fecha no especificada"
                })
                
                print(f"[DEBUG] Imagen {i} procesada:")
                print(f"  - Ruta: {foto_path}")
                print(f"  - URL: {foto_url}")
                print(f"  - Relativa: {relative_url}")
                
            except Exception as e:
                print(f"[ERROR] Error procesando imagen {i}: {str(e)}")
        
        context = {
            'reporte': reporte,
            'fotos': fotos_list,
            'logo_url': logo_url,
            'request': request,
            'debug': settings.DEBUG
        }
        
        # Renderizar la plantilla HTML
        template = get_template('reportes/reporte_pdf.html')
        html_string = template.render(context=context, request=request)
        
        # Función para manejar las rutas de los recursos
        def fetch_resources(uri, rel):
            # Imprimir información de depuración
            print(f"\n[DEBUG] Procesando URI: {uri}")
            
            # Si es una URL de datos (data:image/...)
            if uri.startswith('data:'):
                return uri
                
            # Parsear la URL
            parsed_uri = urlparse(uri)
            
            # Si es una URL local (sin esquema o con esquema file:)
            if not parsed_uri.scheme or parsed_uri.scheme == 'file':
                # Obtener la ruta del sistema de archivos
                if parsed_uri.scheme == 'file':
                    path = parsed_uri.path
                else:
                    path = uri
                
                # Si la ruta comienza con /static/ o /media/
                if path.startswith('/static/'):
                    path = path.replace('/static/', '')
                    full_path = os.path.join(settings.STATIC_ROOT, path)
                elif path.startswith('/media/'):
                    path = path.replace('/media/', '')
                    full_path = os.path.join(settings.MEDIA_ROOT, path)
                else:
                    full_path = os.path.join(settings.BASE_DIR, path.lstrip('/'))
                
                # Verificar si el archivo existe
                if os.path.exists(full_path):
                    print(f"[DEBUG] Archivo encontrado: {full_path}")
                    return full_path
                else:
                    print(f"[ERROR] Archivo no encontrado: {full_path}")
                    return None
            
            # Si es una URL remota, intentar descargarla
            elif parsed_uri.scheme in ('http', 'https'):
                try:
                    import requests
                    response = requests.get(uri)
                    if response.status_code == 200:
                        # Crear un archivo temporal con el contenido
                        import tempfile
                        fd, filename = tempfile.mkstemp()
                        with os.fdopen(fd, 'wb') as f:
                            f.write(response.content)
                        print(f"[DEBUG] Imagen descargada: {uri} -> {filename}")
                        return filename
                except Exception as e:
                    print(f"[ERROR] Error al descargar {uri}: {str(e)}")
            
            # Si no se pudo manejar la URI, devolver None
            print(f"[WARNING] No se pudo manejar la URI: {uri}")
                
            print(f"[ERROR] Archivo no encontrado: {path}")
            return None
        
        # Crear un buffer para el PDF
        result = io.BytesIO()
        
        # Convertir HTML a PDF
        pdf = pisa.CreatePDF(
            src=html_string,
            dest=result,
            encoding='UTF-8',
            link_callback=fetch_resources
        )
        
        if not pdf.err:
            # Obtener el contenido del buffer
            response = HttpResponse(result.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="reporte_{reporte_id}.pdf"'
            return response
        
        # Si hay un error, devolver un mensaje de error
        return HttpResponse('Error al generar el PDF: %s' % pdf.err, status=500)