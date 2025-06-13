from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

def send_notification(subject, template_name, context, to_emails):
    """
    Envía una notificación por correo electrónico.
    
    Args:
        subject (str): Asunto del correo
        template_name (str): Nombre de la plantilla de correo (sin extensión)
        context (dict): Contexto para la plantilla
        to_emails (list): Lista de direcciones de correo electrónico de destino
    """
    # Renderizar plantilla HTML
    html_message = render_to_string(f'emails/{template_name}.html', context)
    
    # Crear versión de texto plano
    plain_message = strip_tags(html_message)
    
    # Enviar correo
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=to_emails,
        html_message=html_message,
        fail_silently=False,
    )

def notify_new_observation(observation):
    """Notifica al usuario asignado sobre una nueva observación."""
    if not observation.asignado_a or not observation.asignado_a.email:
        return
    
    context = {
        'observation': observation,
        'site_url': settings.SITE_URL,
    }
    
    subject = f'Nueva observación asignada: {observation.item}'
    
    send_notification(
        subject=subject,
        template_name='new_observation',
        context=context,
        to_emails=[observation.asignado_a.email]
    )

def notify_levantamiento_submitted(levantamiento):
    """Notifica al editor sobre un nuevo levantamiento pendiente de revisión."""
    if not levantamiento.observacion.creado_por or not levantamiento.observacion.creado_por.email:
        return
    
    context = {
        'levantamiento': levantamiento,
        'observation': levantamiento.observacion,
        'site_url': settings.SITE_URL,
    }
    
    subject = f'Levantamiento pendiente de revisión: {levantamiento.observacion.item}'
    
    send_notification(
        subject=subject,
        template_name='levantamiento_submitted',
        context=context,
        to_emails=[levantamiento.observacion.creado_por.email]
    )

def notify_levantamiento_reviewed(levantamiento):
    """Notifica al visor sobre la revisión de su levantamiento."""
    if not levantamiento.observacion.asignado_a or not levantamiento.observacion.asignado_a.email:
        return
    
    context = {
        'levantamiento': levantamiento,
        'observation': levantamiento.observacion,
        'site_url': settings.SITE_URL,
        'aprobado': levantamiento.estado == 'Aprobado'
    }
    
    status = 'aprobado' if context['aprobado'] else 'rechazado'
    subject = f'Levantamiento {status}: {levantamiento.observacion.item}'
    
    send_notification(
        subject=subject,
        template_name='levantamiento_reviewed',
        context=context,
        to_emails=[levantamiento.observacion.asignado_a.email]
    )
