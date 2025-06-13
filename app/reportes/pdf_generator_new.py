import os
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, 
    Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.units import cm, mm, inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.lib.utils import ImageReader
from django.conf import settings
from datetime import datetime

# Colores personalizados
PRIMARY_COLOR = colors.HexColor('#2c3e50')
SECONDARY_COLOR = colors.HexColor('#3498db')
LIGHT_GRAY = colors.HexColor('#f8f9fa')
BORDER_COLOR = colors.HexColor('#dee2e6')
TEXT_COLOR = colors.HexColor('#212529')

# Márgenes
MARGIN = 2 * cm
PADDING = 0.5 * cm

class ReportePDFGenerator:
    def __init__(self, buffer=None, page_size=A4):
        """Inicializa el generador de PDF.
        
        Args:
            buffer: Buffer opcional para escribir el PDF. Si no se proporciona,
                   se creará uno nuevo al generar el PDF.
            page_size: Tamaño de la página (por defecto A4).
        """
        self.buffer = buffer
        self.page_width, self.page_height = page_size
        self.styles = getSampleStyleSheet()
        self._register_fonts()
        self._define_styles()
    
    def _register_fonts(self):
        """Registra fuentes personalizadas si están disponibles"""
        try:
            font_path = os.path.join(settings.BASE_DIR, 'static', 'fonts', 'arial.ttf')
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont('Arial', font_path))
                pdfmetrics.registerFont(TTFont('Arial-Bold', font_path, 'Bold'))
                return True
            return False
        except Exception as e:
            print(f"Error al cargar fuentes: {e}")
            return False
    
    def _define_styles(self):
        """Define los estilos de párrafo personalizados"""
        # Crear un nuevo objeto de estilos para evitar conflictos
        self.styles = getSampleStyleSheet()
        
        # Función auxiliar para agregar o actualizar estilos
        def add_or_update_style(name, **kwargs):
            if name in self.styles:
                style = self.styles[name]
                for key, value in kwargs.items():
                    setattr(style, key, value)
            else:
                self.styles.add(ParagraphStyle(name=name, **kwargs))
        
        # Estilo para el título principal
        add_or_update_style(
            name='Title',
            fontName='Helvetica-Bold',
            fontSize=16,
            leading=20,
            alignment=TA_CENTER,
            spaceAfter=20,
            textColor=PRIMARY_COLOR
        )
        
        # Estilo para secciones
        add_or_update_style(
            name='Section',
            fontName='Helvetica-Bold',
            fontSize=12,
            leading=14,
            alignment=TA_LEFT,
            spaceAfter=10,
            textColor=PRIMARY_COLOR,
            backColor=LIGHT_GRAY,
            borderWidth=1,
            borderColor=BORDER_COLOR,
            borderPadding=5
        )
        
        # Estilo para etiquetas de campo
        add_or_update_style(
            name='FieldLabel',
            fontName='Helvetica-Bold',
            fontSize=9,
            leading=11,
            alignment=TA_LEFT,
            spaceAfter=2,
            textColor=colors.HexColor('#495057')
        )
        
        # Estilo para valores de campo
        add_or_update_style(
            name='FieldValue',
            fontName='Helvetica',
            fontSize=9,
            leading=11,
            alignment=TA_LEFT,
            spaceAfter=8,
            textColor=TEXT_COLOR,
            leftIndent=5
        )
        
        # Estilo para descripciones de fotos
        add_or_update_style(
            name='PhotoDescription',
            fontName='Helvetica',
            fontSize=8,
            leading=10,
            alignment=TA_CENTER,
            spaceBefore=5,
            textColor=colors.HexColor('#6c757d'),
            fontStyle='italic'  # Use fontStyle instead of fontName for italic
        )
    
    def _create_info_table(self, reporte):
        """Crea la tabla con la información del reporte"""
        # Función auxiliar para obtener atributos de manera segura
        def get_attr(obj, attr, default='N/A'):
            try:
                value = getattr(obj, attr, default)
                if value is None or value == '':
                    return default
                return value
            except:
                return default
                
        # Función para formatear fechas
        def format_date(date_value, default='N/A'):
            try:
                if date_value:
                    return date_value.strftime('%d/%m/%Y')
                return default
            except:
                return default
                
        # Datos del reporte
        proyecto_nombre = getattr(getattr(reporte, 'proyecto', None), 'nombre', 'N/A')
        codigo_proyecto = get_attr(reporte, 'codigo_proyecto')
        cliente = get_attr(reporte, 'cliente')
        contratista = get_attr(reporte, 'contratista')
        fecha_emision = format_date(get_attr(reporte, 'fecha_emision'))
        version_reporte = get_attr(reporte, 'version_reporte', '1.0')
        elaborado_por = get_attr(reporte, 'elaborado_por')
        revisado_por = get_attr(reporte, 'revisado_por')
        inicio_supervision = format_date(get_attr(reporte, 'inicio_supervision'))
        mes_actual_obra = get_attr(reporte, 'mes_actual_obra')
        
        data = [
            ["Proyecto:", proyecto_nombre, "Código:", codigo_proyecto],
            ["Cliente:", cliente, "Contratista:", contratista],
            ["Fecha de emisión:", fecha_emision, "Versión:", version_reporte],
            ["Elaborado por:", elaborado_por, "Revisado por:", revisado_por],
            ["Inicio supervisión:", inicio_supervision, 
             "Mes actual de obra:", str(mes_actual_obra) if mes_actual_obra != 'N/A' else 'N/A']
        ]
        
        # Crear tabla
        table = Table(data, colWidths=[3*cm, 6*cm, 2.5*cm, 6*cm])
        
        # Estilo de la tabla
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TEXTCOLOR', (0, 0), (-1, -1), TEXT_COLOR),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTNAME', (3, 0), (3, -1), 'Helvetica'),
            ('LINEBELOW', (0, -1), (-1, -1), 0.5, BORDER_COLOR),
            ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ('BACKGROUND', (0, 0), (-1, 0), LIGHT_GRAY),
        ]))
        
        return table
    
    def _create_photo_card(self, img_path, description, photo_number):
        """Crea una tarjeta para cada foto con su descripción"""
        try:
            # Contenedor principal
            container = []
            
            # Número de foto
            container.append(Paragraph(
                f"<b>Foto {photo_number}</b>",
                style=self.styles['FieldLabel']
            ))
            
            # Imagen
            try:
                if os.path.exists(img_path):
                    img = Image(img_path, width=7.5*cm, height=5.5*cm, kind='proportional')
                    container.append(img)
                else:
                    container.append(Paragraph(
                        f"<i>Imagen no encontrada: {os.path.basename(img_path)}</i>",
                        self.styles['FieldLabel']
                    ))
            except Exception as img_error:
                container.append(Paragraph(
                    f"<i>Error al cargar la imagen: {str(img_error)}</i>",
                    self.styles['FieldLabel']
                ))
            
            # Descripción (asegurarse de que sea texto y escape caracteres especiales)
            if description and str(description).strip():
                # Limpiar y formatear la descripción
                clean_desc = str(description).strip()
                # Usar comillas rectas para evitar problemas con comillas tipográficas
                clean_desc = clean_desc.replace('"', '').replace('“', '').replace('”', '')
                container.append(Paragraph(
                    f'<i>{clean_desc}</i>',  # Usar etiquetas HTML para el estilo itálico
                    self.styles['PhotoDescription']
                ))
            
            # Crear tabla para el borde
            table = Table([[container]], colWidths=[8*cm])
            table.setStyle(TableStyle([
                ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                ('BACKGROUND', (0, 0), (-1, 0), LIGHT_GRAY),
                ('PADDING', (0, 0), (-1, -1), 5),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            
            return table
            
        except Exception as e:
            # En caso de error, devolver una tabla con el mensaje de error
            error_table = Table([["Error al crear la tarjeta de foto"]], colWidths=[8*cm])
            error_table.setStyle(TableStyle([
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.red),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.red),
                ('PADDING', (0, 0), (-1, -1), 5),
            ]))
            return error_table
        
        return table
    
    def _create_photo_grid(self, fotos):
        """Crea una cuadrícula de fotos (2 columnas)"""
        elements = []
        
        # Asegurarse de que tenemos fotos
        if not fotos:
            return elements
            
        # Procesar las fotos en pares
        for i in range(0, len(fotos), 2):
            row_elements = []
            
            # Primera columna
            if i < len(fotos):
                img_path = fotos[i]['imagen_path'].replace('file://', '')
                try:
                    if os.path.exists(img_path):
                        row_elements.append(self._create_photo_card(
                            img_path, 
                            fotos[i].get('descripcion', ''), 
                            i + 1
                        ))
                    else:
                        row_elements.append(Paragraph(
                            f"<i>Imagen no encontrada: {os.path.basename(img_path)}</i>", 
                            self.styles['FieldLabel']
                        ))
                except Exception as e:
                    row_elements.append(Paragraph(
                        f"<i>Error al cargar la imagen: {str(e)}</i>",
                        self.styles['FieldLabel']
                    ))
            
            # Espacio entre columnas
            if i + 1 < len(fotos):
                row_elements.append(Spacer(0.5*cm, 0))
                
                # Segunda columna
                img_path = fotos[i+1]['imagen_path'].replace('file://', '')
                try:
                    if os.path.exists(img_path):
                        row_elements.append(self._create_photo_card(
                            img_path, 
                            fotos[i+1].get('descripcion', ''), 
                            i + 2
                        ))
                    else:
                        row_elements.append(Paragraph(
                            f"<i>Imagen no encontrada: {os.path.basename(img_path)}</i>", 
                            self.styles['FieldLabel']
                        ))
                except Exception as e:
                    row_elements.append(Paragraph(
                        f"<i>Error al cargar la imagen: {str(e)}</i>",
                        self.styles['FieldLabel']
                    ))
            
            # Agregar la fila a los elementos
            if row_elements:
                # Crear una tabla con 2 columnas para la fila actual
                row_table = Table([row_elements], colWidths=['50%', '50%'])
                row_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ]))
                
                elements.append(row_table)
                elements.append(Spacer(1, 0.8*cm))  # Espacio entre filas
        
        return elements
    
    def _create_header(self, reporte):
        """Crea el encabezado con el logo y el título"""
        try:
            # Ruta al logo (ajusta según tu estructura de archivos)
            logo_path = os.path.join('app', 'static', 'img', 'logo_jlv.jpg')
            
            # Verificar si el archivo del logo existe
            if not os.path.exists(logo_path):
                # Intentar con la ruta alternativa
                logo_path = os.path.join('app', 'staticfiles', 'img', 'logo_jlv.jpg')
                if not os.path.exists(logo_path):
                    return None
            
            # Cargar la imagen del logo
            logo = Image(logo_path, width=2.5*cm, height=2.5*cm, kind='proportional')
            
            # Crear una tabla para el encabezado con 2 columnas
            header_data = [
                [logo, ''],  # Logo en la primera columna, espacio en blanco en la segunda
            ]
            
            header_table = Table(header_data, colWidths=[3*cm, 12*cm])
            header_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('ALIGN', (1, 0), (1, 0), 'CENTER'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ]))
            
            return header_table
            
        except Exception as e:
            print(f"Error al cargar el logo: {str(e)}")
            return None
    
    def generate_pdf(self, reporte, fotos):
        """Genera el PDF completo"""
        elements = []
        
        # Crear un nuevo buffer para este PDF
        buffer = BytesIO()
        
        try:
            # Crear el documento
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=MARGIN,
                leftMargin=MARGIN,
                topMargin=MARGIN,
                bottomMargin=MARGIN
            )
            
            # Agregar el encabezado con el logo
            header = self._create_header(reporte)
            if header:
                elements.append(header)
            
            # Título del reporte
            title_text = reporte.get_tipo_formulario_display() or 'REPORTE FOTOGRÁFICO'
            title = Paragraph(f'<para align=center><b>{title_text}</b></para>', self.styles['Title'])
            elements.append(title)
            elements.append(Spacer(1, 0.5*cm))
            
            # Tabla de información del reporte
            elements.append(self._create_info_table(reporte))
            elements.append(Spacer(1, 0.5*cm))
            
            # Sección de descripción si existe
            if reporte.descripcion:
                elements.append(Paragraph("<b>Descripción:</b>", self.styles['FieldLabel']))
                elements.append(Paragraph(reporte.descripcion, self.styles['FieldValue']))
                elements.append(Spacer(1, 0.5*cm))
            
            # Sección de fotos
            if fotos:
                section_title = Paragraph("<b>REGISTRO FOTOGRÁFICO</b>", self.styles['Section'])
                elements.append(section_title)
                elements.append(Spacer(1, 0.5*cm))
                
                # Agregar las fotos en una cuadrícula
                photo_grid = self._create_photo_grid(fotos)
                if photo_grid:
                    elements.extend(photo_grid)
            
            # Construir el documento
            doc.build(elements)
            
            # Obtener el valor del buffer
            pdf = buffer.getvalue()
            return pdf
            
        except Exception as e:
            print(f"Error en generate_pdf: {str(e)}")
            raise
            
        finally:
            # Cerrar el buffer
            if not buffer.closed:
                buffer.close()
