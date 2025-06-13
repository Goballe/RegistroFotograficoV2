from django.db import models
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
# Use string reference to avoid circular import
# from reportes.models import Proyecto  # Removed to avoid circular import


class PuntoInspeccion(models.TextChoices):
    SELECCIONAR = '', '---------'
    ALMACENAMIENTO = 'Almacenamiento de materiales', 'Almacenamiento de materiales'
    CALIBRACION = 'Calibración de equipos', 'Calibración de equipos'
    ENSAYOS = 'Ensayos y pruebas', 'Ensayos y pruebas'
    ESTRUCTURAS = 'Partidas de estructuras', 'Partidas de estructuras'
    ARQUITECTURA = 'Partidas de arquitectura', 'Partidas de arquitectura'
    IISS = 'Partidas de IISS', 'Partidas de IISS'
    IIEE = 'Partidas de IIEE', 'Partidas de IIEE'
    IIIM = 'Partidas de IIMM', 'Partidas de IIMM'
    GESTION_CALIDAD = 'Gestión de calidad', 'Gestión de calidad'
    LECCIONES = 'Lecciones Aprendidas', 'Lecciones Aprendidas'


class SubClasificacion(models.TextChoices):
    SELECCIONAR = '', '---------'
    MATERIALES_EXPUESTOS = 'Materiales expuestos', 'Materiales expuestos'
    ORDENAMIENTO = 'Ordenamiento de materiales', 'Ordenamiento de materiales'
    VERIFICACION = 'Verificación de calibración', 'Verificación de calibración'
    REQUERIMIENTO = 'Requerimiento de pruebas', 'Requerimiento de pruebas'
    MURO = 'Muro anclado', 'Muro anclado'
    ACERO = 'Acero', 'Acero'
    ENCOFRADO = 'Encofrado', 'Encofrado'
    CONCRETO = 'Concreto', 'Concreto'
    CURADO = 'Curado', 'Curado'
    EMPASTADO = 'Empastado y/o Pintura', 'Empastado y/o Pintura'
    CERAMICO = 'Cerámico y/o Porcelanato', 'Cerámico y/o Porcelanato'
    TUBERIAS = 'Recorrido de tuberías', 'Recorrido de tuberías'
    OBSTRUCCION = 'Obstrucción de tuberías', 'Obstrucción de tuberías'
    PRUEBAS = 'Pruebas y Funcionamiento', 'Pruebas y Funcionamiento'
    PLANOS = 'Planos sin sello', 'Planos sin sello'


class ObservacionCalidad(models.Model):
    """
    Modelo para almacenar las observaciones de calidad en los proyectos.
    """
    class NivelRiesgo(models.TextChoices):
        ALTO = 'Alto', 'Alto'
        MEDIO = 'Medio', 'Medio'
        BAJO = 'Bajo', 'Bajo'
    
    class EstadoObservacion(models.TextChoices):
        PENDIENTE = 'Pendiente', 'Pendiente'
        EN_PROCESO = 'En Proceso', 'En Proceso'
        ATENDIDO = 'Atendido', 'Atendido'
        CERRADO = 'Cerrado', 'Cerrado'
    
    proyecto = models.ForeignKey('reportes.Proyecto', on_delete=models.CASCADE, related_name='observaciones_calidad')
    item = models.CharField('Ítem', max_length=50)
    asignado_a = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='observaciones_asignadas',
        verbose_name='Asignado a',
        help_text='Usuario responsable de realizar el levantamiento de esta observación.'
    )
    semana_obs = models.CharField('Semana de Observación', max_length=20)
    
    fecha = models.DateField('Fecha', default=timezone.now)
    punto_inspeccion = models.CharField(
        'Punto de Inspección',
        max_length=50,
        choices=PuntoInspeccion.choices,
        default=PuntoInspeccion.SELECCIONAR,
        blank=True,
        help_text='Selecciona un punto de inspección de la lista'
    )
    sub_clasificacion = models.CharField(
        'Sub Clasificación',
        max_length=100,
        choices=SubClasificacion.choices,
        default=SubClasificacion.SELECCIONAR,
        blank=True,
        help_text='Selecciona una sub clasificación de la lista'
    )
    descripcion = models.TextField('Descripción de la Observación')
    nivel_riesgo = models.CharField('Nivel de Riesgo', max_length=10, choices=NivelRiesgo.choices)
    recomendacion = models.TextField('Recomendación para Levantamiento')
    estado = models.CharField('Estado', max_length=20, choices=EstadoObservacion.choices, default=EstadoObservacion.PENDIENTE)
    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='observaciones_creadas')
    creado_en = models.DateTimeField('Creado en', auto_now_add=True)
    actualizado_en = models.DateTimeField('Actualizado en', auto_now=True)
    
    # Campos para fotos (almacenamiento en el sistema de archivos)
    foto_1 = models.ImageField('Fotografía 01', upload_to='observaciones/calidad/', null=True, blank=True)
    foto_2 = models.ImageField('Fotografía 02', upload_to='observaciones/calidad/', null=True, blank=True)
    
    class Meta:
        verbose_name = 'Observación de Calidad'
        verbose_name_plural = 'Observaciones de Calidad'
        unique_together = ('proyecto', 'item')
        ordering = ['proyecto', 'item']
    
    def __str__(self):
        return f"{self.proyecto.nombre if hasattr(self, 'proyecto') and self.proyecto else 'Proyecto no disponible'} - {self.item} - {self.estado}"


class TipoObservacionSSOMA(models.TextChoices):
    SELECCIONAR = '', '---------'
    CONDICION_INSEGURA = 'Condición Insegura', 'Condición Insegura'
    ACTO_INSEGURO = 'Acto Inseguro', 'Acto Inseguro'
    INCUMPLIMIENTO_NORMA = 'Incumplimiento de Norma', 'Incumplimiento de Norma'
    OBSERVACION_PREVENTIVA = 'Observación Preventiva', 'Observación Preventiva'


class AreaSSOMA(models.TextChoices):
    SELECCIONAR = '', '---------'
    AREA_ADMINISTRATIVA = 'Área Administrativa', 'Área Administrativa'
    ALMACEN = 'Almacén', 'Almacén'
    TALLER = 'Taller', 'Taller'
    OBRA_CIVIL = 'Obra Civil', 'Obra Civil'
    INSTALACIONES_ELECTRICAS = 'Instalaciones Eléctricas', 'Instalaciones Eléctricas'
    INSTALACIONES_SANITARIAS = 'Instalaciones Sanitarias', 'Instalaciones Sanitarias'
    AREAS_COMUNES = 'Áreas Comunes', 'Áreas Comunes'


class PuntoInspeccionSSOMA(models.TextChoices):
    SELECCIONAR = '', '---------'
    TRABAJOS_CIVILES = 'Trabajos civiles', 'Trabajos civiles'
    EXCAVACION = 'Trabajos de excavación y/o movimiento de tierra', 'Trabajos de excavación y/o movimiento de tierra'
    ELECTRICOS = 'Trabajos eléctricos', 'Trabajos eléctricos'
    ALTURA = 'Trabajos en altura', 'Trabajos en altura'
    ACABADOS = 'Acabados/Arquitectura', 'Acabados/Arquitectura'
    TRANSPORTE = 'Transporte y carga', 'Transporte y carga'
    SANITARIOS = 'Trabajos sanitarios', 'Trabajos sanitarios'
    IZAJE = 'Trabajos de izaje', 'Trabajos de izaje'
    GESTION_SEGURIDAD = 'Gestión de seguridad', 'Gestión de seguridad'
    GESTION_AMBIENTAL = 'Gestión ambiental', 'Gestión ambiental'
    OTROS = 'Otros-S', 'Otros-S'

class SubClasificacionSSOMA(models.TextChoices):
    SELECCIONAR = '', '---------'
    BIENESTAR = 'Servicios de bienestar', 'Servicios de bienestar'
    ORGANIZACION = 'Organización de las áreas de trabajo', 'Organización de las áreas de trabajo'
    ELECTRICAS = 'Instalaciones eléctricas provisionales', 'Instalaciones eléctricas provisionales'
    ACCESOS = 'Accesos y vías de circulación', 'Accesos y vías de circulación'
    MATERIALES = 'Identificación de materiales', 'Identificación de materiales'
    SEÑALIZACION = 'Señalización, orden y limpieza', 'Señalización, orden y limpieza'
    ILUMINACION = 'Iluminación', 'Iluminación'
    RESIDUOS = 'Segregación de residuos', 'Segregación de residuos'
    INSPECCION = 'Inspección de seguridad', 'Inspección de seguridad'
    EMERGENCIAS = 'Equipos de respuesta a emergencia', 'Equipos de respuesta a emergencia'
    ACTO_INSEGURO = 'Acto inseguro', 'Acto inseguro'
    CONDICION_INSEGURA = 'Condición insegura', 'Condición insegura'
    EPP = 'Uso de EPPs', 'Uso de EPPs'
    DOCUMENTACION = 'Documentación', 'Documentación'
    OTROS = 'Otros-S', 'Otros-S'

class ObservacionSeguridadSSOMA(models.Model):
    """
    Modelo para almacenar las observaciones de seguridad SSOMA en los proyectos.
    """
    class NivelRiesgo(models.TextChoices):
        ALTO = 'Alto', 'Alto'
        MEDIO = 'Medio', 'Medio'
        BAJO = 'Bajo', 'Bajo'
    
    class EstadoObservacion(models.TextChoices):
        PENDIENTE = 'Pendiente', 'Pendiente'
        EN_PROCESO = 'En Proceso', 'En Proceso'
        ATENDIDO = 'Atendido', 'Atendido'
        CERRADO = 'Cerrado', 'Cerrado'
    
    proyecto = models.ForeignKey('reportes.Proyecto', on_delete=models.CASCADE, related_name='observaciones_ssoma')
    item = models.CharField('Ítem', max_length=50)
    punto_inspeccion = models.CharField(
        'Punto de Inspección',
        max_length=100,
        choices=PuntoInspeccionSSOMA.choices,
        default=PuntoInspeccionSSOMA.SELECCIONAR,
        help_text='Seleccione el punto de inspección'
    )
    subclasificacion = models.CharField(
        'Subclasificación',
        max_length=100,
        choices=SubClasificacionSSOMA.choices,
        default=SubClasificacionSSOMA.SELECCIONAR,
        help_text='Seleccione la subclasificación'
    )
    tipo_observacion = models.CharField(
        'Tipo de Observación',
        max_length=50,
        choices=TipoObservacionSSOMA.choices,
        default=TipoObservacionSSOMA.SELECCIONAR,
        help_text='Seleccione el tipo de observación de seguridad'
    )
    area = models.CharField(
        'Área',
        max_length=50,
        choices=AreaSSOMA.choices,
        default=AreaSSOMA.SELECCIONAR,
        help_text='Seleccione el área donde se realizó la observación'
    )
    asignado_a = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='observaciones_ssoma_asignadas',
        verbose_name='Responsable',
        help_text='Persona responsable de atender la observación'
    )
    semana_obs = models.CharField('Semana de Observación', max_length=20)
    fecha = models.DateField('Fecha', default=timezone.now)
    descripcion = models.TextField('Descripción de la Observación')
    accion_correctiva = models.TextField('Acción Correctiva Propuesta')
    nivel_riesgo = models.CharField('Nivel de Riesgo', max_length=10, choices=NivelRiesgo.choices)
    fecha_compromiso = models.DateField('Fecha de Compromiso', null=True, blank=True)
    estado = models.CharField('Estado', max_length=20, choices=EstadoObservacion.choices, default=EstadoObservacion.PENDIENTE)
    
    # Campos para evidencias fotográficas
    foto_1 = models.ImageField('Fotografía 01', upload_to='observaciones/ssoma/', null=True, blank=True)
    foto_2 = models.ImageField('Fotografía 02', upload_to='observaciones/ssoma/', null=True, blank=True)
    
    # Auditoría
    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='observaciones_ssoma_creadas')
    creado_en = models.DateTimeField('Creado en', auto_now_add=True)
    actualizado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='observaciones_ssoma_actualizadas')
    actualizado_en = models.DateTimeField('Actualizado en', auto_now=True)
    
    class Meta:
        verbose_name = 'Control de Observaciones de Seguridad'
        verbose_name_plural = 'Control de Observaciones de Seguridad'
        unique_together = ('proyecto', 'item')
        ordering = ['-fecha', 'proyecto', 'item']
    
    def __str__(self):
        return f"{self.proyecto.nombre if hasattr(self, 'proyecto') and self.proyecto else 'Proyecto no disponible'} - {self.item} - {self.get_tipo_observacion_display()}"
    
    def get_absolute_url(self):
        return reverse('obervaciones:ver_observacion_ssoma', kwargs={'proyecto_id': self.proyecto.id, 'pk': self.pk})


# -------------------- Modelo Levantamiento para Observaciones SSOMA --------------------
class LevantamientoSSOMA(models.Model):
    """Representa el levantamiento realizado por un VISOR sobre una observación SSOMA.

    Está ligado 1-a-1 con la observación original. Posteriormente un EDITOR lo revisa y
    decide si se aprueba o se rechaza. Esta tabla almacena tanto la data ingresada por
    el VISOR como la resolución del EDITOR.
    """

    class Estado(models.TextChoices):
        PENDIENTE = "Pendiente", "Pendiente de revisión"
        APROBADO = "Aprobado", "Aprobado"
        RECHAZADO = "Rechazado", "Rechazado"

    observacion = models.OneToOneField(
        "obervaciones.ObservacionSeguridadSSOMA",
        on_delete=models.CASCADE,
        related_name="levantamiento",
    )

    # Datos ingresados por el VISOR
    semana_levantamiento = models.CharField("Semana de levantamiento", max_length=20)
    fecha_levantamiento = models.DateField("Fecha de levantamiento", default=timezone.now)
    descripcion = models.TextField("Descripción del levantamiento")
    fotografia = models.ImageField(
        "Fotografía",
        upload_to="levantamientos/",
        null=True,
        blank=True,
    )
    tiempo_levantamiento = models.DurationField("Tiempo de levantamiento")

    # Datos de la revisión (EDITOR)
    estado = models.CharField(
        "Estado de revisión",
        max_length=20,
        choices=Estado.choices,
        default=Estado.PENDIENTE,
    )
    comentario_revisor = models.TextField("Comentario del revisor", blank=True)
    revisor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="levantamientos_ssoma_revisados",
    )
    revisado_en = models.DateTimeField("Revisado en", null=True, blank=True)

    class Meta:
        verbose_name = "Levantamiento de Observación (SSOMA)"
        verbose_name_plural = "Levantamientos de Observaciones (SSOMA)"
        ordering = ["-fecha_levantamiento"]

    def __str__(self):
        return f"Levantamiento {self.observacion.item} – {self.get_estado_display()}"


# -------------------- Modelo Levantamiento para Observaciones de Calidad --------------------
class LevantamientoObservacion(models.Model):
    """Representa el levantamiento realizado por un VISOR sobre una observación de CALIDAD.

    Está ligado 1-a-1 con la observación original. Posteriormente un EDITOR lo revisa y
    decide si se aprueba o se rechaza. Esta tabla almacena tanto la data ingresada por
    el VISOR como la resolución del EDITOR.
    """
    class Estado(models.TextChoices):
        PENDIENTE = "Pendiente", "Pendiente de revisión"
        APROBADO = "Aprobado", "Aprobado"
        RECHAZADO = "Rechazado", "Rechazado"

    observacion = models.OneToOneField(
        "obervaciones.ObservacionCalidad",
        on_delete=models.CASCADE,
        related_name="levantamiento",
    )

    # Datos ingresados por el VISOR
    semana_levantamiento = models.CharField("Semana de levantamiento", max_length=20)
    fecha_levantamiento = models.DateField("Fecha de levantamiento", default=timezone.now)
    descripcion = models.TextField("Descripción del levantamiento")
    fotografia = models.ImageField(
        "Fotografía",
        upload_to="levantamientos/",
        null=True,
        blank=True,
    )
    tiempo_levantamiento = models.DurationField("Tiempo de levantamiento")

    # Datos de la revisión (EDITOR)
    estado = models.CharField(
        "Estado de revisión",
        max_length=20,
        choices=Estado.choices,
        default=Estado.PENDIENTE,
    )
    comentario_revisor = models.TextField("Comentario del revisor", blank=True)
    revisor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="levantamientos_revisados",
    )
    revisado_en = models.DateTimeField("Revisado en", null=True, blank=True)

    class Meta:
        verbose_name = "Levantamiento de Observación (Calidad)"
        verbose_name_plural = "Levantamientos de Observaciones (Calidad)"
        ordering = ["-fecha_levantamiento"]

    def __str__(self):
        return f"Levantamiento {self.observacion.item} – {self.get_estado_display()}"


# ---------------------------------------------------------------------------
# Modelo y señales para notificaciones a usuarios del grupo "visores"
# ---------------------------------------------------------------------------

class Notificacion(models.Model):
    """Notificación simple para mostrar mensajes a los usuarios."""

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notificaciones",
    )
    mensaje = models.CharField(max_length=255)
    url = models.CharField(max_length=255)
    leida = models.BooleanField(default=False)
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creada_en"]

    def __str__(self):
        return f"Notif → {self.usuario}: {self.mensaje[:50]}"


# ----------------------- señales ------------------------------------------

def _crear_notificaciones_para_visores(mensaje: str, url: str):
    """Crea instancias de Notificacion para todos los usuarios visores activos."""
    UserModel = get_user_model()
    visores = UserModel.objects.filter(groups__name="visores", is_active=True)

    bulk_objs = [
        Notificacion(usuario=u, mensaje=mensaje, url=url)
        for u in visores
    ]
    if bulk_objs:
        Notificacion.objects.bulk_create(bulk_objs)

def _crear_notificaciones_para_editores(mensaje: str, url: str):
    """Crea instancias de Notificacion para todos los usuarios editores activos."""
    UserModel = get_user_model()
    editores = UserModel.objects.filter(groups__name="editores", is_active=True)

    bulk_objs = [
        Notificacion(usuario=u, mensaje=mensaje, url=url)
        for u in editores
    ]
    if bulk_objs:
        Notificacion.objects.bulk_create(bulk_objs)

# Señales post_save para ObservacionSeguridadSSOMA y ObservacionCalidad

@receiver(post_save, sender="obervaciones.ObservacionSeguridadSSOMA")
@receiver(post_save, sender="obervaciones.ObservacionCalidad")
def crear_notificacion_observacion(sender, instance, created, **kwargs):
    if not created:
        return  # Solo al crear

    # Solo si la observación está en estado pendiente
    try:
        estado = instance.estado
    except AttributeError:
        estado = getattr(instance, "estado", None)

    if estado and estado != "Pendiente":
        return

    proyecto_nombre = instance.proyecto.nombre if hasattr(instance, 'proyecto') and instance.proyecto else "Proyecto"
    mensaje = f"Nueva observación pendiente ({instance.item}) en {proyecto_nombre}"
    try:
        url = instance.get_absolute_url()
    except Exception:
        url = reverse("obervaciones:lista_observaciones", kwargs={"proyecto_id": instance.proyecto.id})

    _crear_notificaciones_para_visores(mensaje, url)
    _crear_notificaciones_para_editores(mensaje, url)
