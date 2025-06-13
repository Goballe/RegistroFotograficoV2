import os
from io import BytesIO
from django.conf import settings
from django.utils import timezone
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image as PILImage

class ObservacionPDFGenerator:
    def __init__(self, buffer=None):
        self.buffer = buffer if buffer else BytesIO()
        self.page_width, self.page_height = letter
        self.styles = getSampleStyleSheet()
        self._register_fonts()
        self._register_custom_styles()
    
    def _register_fonts(self):
        """Registra las fuentes personalizadas si están disponibles."""
        try:
            # Intentar registrar Century Gothic
            pdfmetrics.registerFont(TTFont('CenturyGothic', 'c:/windows/fonts/gothic.ttf'))
            pdfmetrics.registerFont(TTFont('CenturyGothic-Bold', 'c:/windows/fonts/gothicb.ttf'))
            self.font_name = 'CenturyGothic'
            self.bold_font_name = 'CenturyGothic-Bold'
        except:
            # Si falla, usar Arial como respaldo
            try:
                pdfmetrics.registerFont(TTFont('Arial', 'c:/windows/fonts/arial.ttf'))
                pdfmetrics.registerFont(TTFont('Arial-Bold', 'c:/windows/fonts/arialbd.ttf'))
                self.font_name = 'Arial'
                self.bold_font_name = 'Arial-Bold'
            except:
                # Si todo falla, usar fuentes estándar
                self.font_name = 'Helvetica'
                self.bold_font_name = 'Helvetica-Bold'
    
    def _register_custom_styles(self):
        """Registra estilos personalizados para el PDF."""
        # Crear estilo Normal si no existe
        if 'Normal' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='Normal',
                fontName=self.font_name,
                fontSize=10,
                leading=12,
                textColor=colors.black
            ))
        
        # Crear estilo Title si no existe
        if 'Title' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='Title',
                fontName=self.bold_font_name,
                fontSize=16,
                leading=22,
                alignment=1,  # Centrado
                spaceAfter=20,
                textColor=colors.HexColor('#333333')
            ))
        
        # Crear estilo Subtitle si no existe
        if 'Subtitle' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='Subtitle',
                fontName=self.bold_font_name,
                fontSize=12,
                leading=16,
                spaceAfter=10,
                textColor=colors.HexColor('#444444')
            ))
        
        # Crear estilo Header si no existe
        if 'Header' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='Header',
                fontName=self.bold_font_name,
                fontSize=10,
                leading=12,
                textColor=colors.white,
                backColor=colors.HexColor('#92263f'),
                alignment=1,  # Centrado
                padding=6,
                spaceAfter=10
            ))
    
    def _create_header(self, elements, observacion):
        """Crea el encabezado del PDF con el logo y la información del proyecto."""
        # Logo
        logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'Logo-JLV2.png')
        if os.path.exists(logo_path):
            logo = Image(logo_path, width=100, height=50)
            elements.append(logo)
        
        # Título
        title = Paragraph("DETALLE DE OBSERVACIÓN", self.styles['Title'])
        elements.append(title)
        
        # Información general
        data = [
            ["PROYECTO:", observacion.proyecto.nombre],
            ["FECHA:", observacion.fecha.strftime('%d/%m/%Y')],
            ["ESTADO:", observacion.get_estado_display()],
            ["NIVEL DE RIESGO:", observacion.get_nivel_riesgo_display()]
        ]
        
        table_style = [
            ('FONT', (0, 0), (-1, -1), self.font_name, 10),
            ('FONT', (0, 0), (0, -1), self.bold_font_name, 10),  # Primera columna en negrita
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dddddd')),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f5f5f5')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#666666')),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]
        
        table = Table(data, colWidths=[100, None])
        table.setStyle(TableStyle(table_style))
        elements.append(table)
        elements.append(Spacer(1, 20))
    
    def _create_section(self, elements, title, content):
        """Crea una sección del PDF con título y contenido."""
        elements.append(Paragraph(title, self.styles['Subtitle']))
        elements.append(Spacer(1, 5))
        
        if isinstance(content, list):
            for item in content:
                elements.append(Paragraph(f"• {item}", self.styles['Normal']))
        else:
            elements.append(Paragraph(content, self.styles['Normal']))
        
        elements.append(Spacer(1, 10))
    
    def _create_photos_section(self, elements, observacion):
        """Crea la sección de fotos de la observación."""
        photos = []
        if observacion.foto_1:
            photos.append(observacion.foto_1.path)
        if observacion.foto_2:
            photos.append(observacion.foto_2.path)
        
        if not photos:
            return
        
        elements.append(Paragraph("FOTOGRAFÍAS", self.styles['Subtitle']))
        elements.append(Spacer(1, 5))
        
        # Ajustar el tamaño de las imágenes para que quepan en la página
        img_width = (self.page_width - 2 * inch) / 2
        img_height = img_width * 0.75  # Relación de aspecto 4:3
        
        photo_data = []
        for i, photo_path in enumerate(photos, 1):
            if os.path.exists(photo_path):
                try:
                    img = Image(photo_path, width=img_width, height=img_height)
                    photo_data.append([f"Foto {i}", img])
                except:
                    photo_data.append([f"Foto {i} (No disponible)", ""])
            else:
                photo_data.append([f"Foto {i} (No disponible)", ""])
        
        # Crear una tabla con las fotos
        table_style = [
            ('FONT', (0, 0), (-1, -1), self.font_name, 8),
            ('FONT', (0, 0), (-1, 0), self.bold_font_name, 8),  # Encabezado en negrita
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dddddd')),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#92263f')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]
        
        # Agregar las fotos en filas de 2
        for i in range(0, len(photo_data), 2):
            row = photo_data[i:i+2]
            # Asegurar que siempre haya 2 columnas
            while len(row) < 2:
                row.append(["", ""])
            table = Table([
                [row[0][0], row[1][0]],
                [row[0][1], row[1][1]]
            ], colWidths=[img_width, img_width])
            table.setStyle(TableStyle(table_style))
            elements.append(table)
            elements.append(Spacer(1, 10))
    
    def _truncate_text(self, text, max_length=250):
        """Trunca el texto si excede la longitud máxima."""
        if not text:
            return ""
        if len(text) > max_length:
            return text[:max_length-3] + "..."
        return text

    def generate_pdf(self, observacion, levantamiento=None):
        """Genera el PDF con los detalles de la observación en una sola página."""
        try:
            # Crear el documento PDF con márgenes mínimos
            doc = SimpleDocTemplate(
                self.buffer,
                pagesize=letter,
                rightMargin=15,  # Reducido de 30
                leftMargin=15,   # Reducido de 30
                topMargin=20,    # Reducido de 40
                bottomMargin=15  # Reducido de 30
            )
            
            elements = []
            
            # Logo más pequeño
            logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'Logo-JLV2.png')
            if os.path.exists(logo_path):
                try:
                    logo = Image(logo_path, width=80, height=40)  # Reducido de 120x60
                    logo.hAlign = 'CENTER'
                    elements.append(logo)
                    elements.append(Spacer(1, 5))  # Reducido de 10
                except Exception as e:
                    print(f"Error al cargar el logo: {str(e)}")
            
            # Título más compacto
            title_style = ParagraphStyle(
                'Title',
                parent=self.styles['Title'],
                fontSize=14,
                spaceAfter=8,
                alignment=1,
                textColor=colors.HexColor('#333333'),
                fontName=self.bold_font_name
            )
            title = Paragraph("DETALLE DE OBSERVACIÓN", title_style)
            elements.append(title)
            elements.append(Spacer(1, 5))  # Reducido de 10
            
            # Estilo para la tabla de información más compacta
            table_style = TableStyle([
                ('FONT', (0, 0), (-1, -1), self.font_name, 8),
                ('FONT', (0, 0), (0, -1), self.bold_font_name, 8),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#eeeeee')),  # Línea más clara
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#eeeeee')),
                ('PADDING', (0, 0), (-1, -1), 2),  # Reducido de 4
                ('LEFTPADDING', (0, 0), (0, -1), 4),  # Reducido de 6
                ('RIGHTPADDING', (-1, 0), (-1, -1), 4),  # Reducido de 6
            ])
            
            # Tabla de información general
            info_data = [
                ["Proyecto:", observacion.proyecto.nombre],
                ["Ítem:", observacion.item],
                ["Fecha:", observacion.fecha.strftime('%d/%m/%Y')],
                ["Estado:", observacion.get_estado_display()],
                ["Nivel de Riesgo:", observacion.get_nivel_riesgo_display()],
                ["Asignado a:", observacion.asignado_a.get_full_name() if observacion.asignado_a else 'No asignado'],
            ]
            
            info_table = Table(info_data, colWidths=['30%', '70%'])
            info_table.setStyle(table_style)
            elements.append(info_table)
            elements.append(Spacer(1, 12))
            
            # Estilo para párrafos más compacto
            desc_style = ParagraphStyle(
                'Descripcion',
                parent=self.styles['Normal'],
                fontSize=8,  # Reducido de 9
                leading=10,  # Reducido de 11
                spaceAfter=4  # Reducido de 8
            )
            
            # Estilo para subtítulos más compactos
            subtitle_style = ParagraphStyle(
                'Subtitle',
                parent=self.styles['Subtitle'],
                fontSize=9,  # Reducido de 10
                spaceAfter=2,  # Reducido de 4
                textColor=colors.HexColor('#333333'),
                spaceBefore=4  # Espacio antes del subtítulo
            )
            
            elements.append(Paragraph("<b>DESCRIPCIÓN</b>", subtitle_style))
            elements.append(Paragraph(observacion.descripcion or "Sin descripción", desc_style))
            elements.append(Spacer(1, 8))
            
            # Sección de recomendación
            elements.append(Paragraph("<b>RECOMENDACIÓN</b>", subtitle_style))
            elements.append(Paragraph(observacion.recomendacion or "Sin recomendación", desc_style))
            
            # Fotos si existen
            photos = []
            if observacion.foto_1 and os.path.exists(observacion.foto_1.path):
                photos.append(observacion.foto_1.path)
            if observacion.foto_2 and os.path.exists(observacion.foto_2.path):
                photos.append(observacion.foto_2.path)
            
            if photos:
                elements.append(Spacer(1, 8))
                elements.append(Paragraph("<b>FOTOGRAFÍAS</b>", subtitle_style))
                
                # Tamaño máximo de las imágenes
                # Tamaño de las imágenes (más pequeñas para que todo quepa en una página)
                max_width = 2.0 * inch  # Reducido de 2.2
                max_height = 1.4 * inch  # Reducido de 1.6
                
                # Mostrar hasta 2 fotos en una fila
                if photos:
                    img_table_data = []
                    row = []
                    
                    for i, photo_path in enumerate(photos[:2]):
                        try:
                            # Redimensionar manteniendo la relación de aspecto
                            img = Image(photo_path)
                            img_width, img_height = img.drawWidth, img.drawHeight
                            ratio = min(max_width/img_width, max_height/img_height)
                            img = Image(photo_path, width=img_width*ratio, height=img_height*ratio)
                            row.append(img)
                        except Exception as e:
                            row.append(Paragraph(f"Error al cargar la imagen", desc_style))
                    
                    # Crear tabla con las imágenes y espaciado
                    img_table = Table([row], colWidths=[max_width]*len(row))
                    img_table.setStyle(TableStyle([
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('PADDING', (0, 0), (-1, -1), 10),  # Espaciado interno
                        ('LEFTPADDING', (0, 0), (0, -1), 10),  # Espacio a la izquierda de la primera imagen
                        ('RIGHTPADDING', (-1, 0), (-1, -1), 10),  # Espacio a la derecha de la última imagen
                        ('SPAN', (0, 0), (0, 0)),  # Para asegurar que el espaciado se aplique correctamente
                    ]))
                    
                    # Añadir espacio entre las imágenes si hay más de una
                    if len(row) > 1:
                        img_table.setStyle(TableStyle([
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('PADDING', (0, 0), (-1, -1), 10),
                            ('LEFTPADDING', (0, 0), (0, -1), 10),
                            ('RIGHTPADDING', (-1, 0), (-1, -1), 10),
                            ('SPAN', (0, 0), (0, 0)),
                            # Añadir espacio entre columnas (entre imágenes)
                            ('TOPPADDING', (0, 0), (-1, -1), 0),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                            ('LEFTPADDING', (1, 0), (1, 0), 20),  # Espacio entre imágenes
                        ]))
                    elements.append(img_table)
            
            # Información del levantamiento si existe
            if levantamiento:
                elements.append(Spacer(1, 10))
                
                # Crear una sección más compacta para el levantamiento
                lev_data = [
                    ["Estado:", levantamiento.get_estado_display()],
                    ["Fecha:", levantamiento.fecha_levantamiento.strftime('%d/%m/%Y')],
                    ["Realizado por:", levantamiento.creado_por.get_full_name() if levantamiento.creado_por else 'No especificado'],
                ]
                
                # Tabla más compacta
                lev_table = Table(lev_data, colWidths=['25%', '75%'])
                lev_table.setStyle(TableStyle([
                    ('FONT', (0, 0), (-1, -1), self.font_name, 8),
                    ('FONT', (0, 0), (0, -1), self.bold_font_name, 8),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('TOPPADDING', (0, 0), (-1, -1), 2),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                    ('LEFTPADDING', (0, 0), (0, -1), 0),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#eeeeee')),
                ]))
                
                elements.append(lev_table)
                
                # Agregar descripción del levantamiento si existe
                if levantamiento.descripcion:
                    elements.append(Spacer(1, 8))
                    elements.append(Paragraph("<b>DESCRIPCIÓN DEL LEVANTAMIENTO</b>", subtitle_style))
                    elements.append(Paragraph(levantamiento.descripcion, desc_style))
                
                # Agregar foto del levantamiento si existe
                if levantamiento.fotografia and os.path.exists(levantamiento.fotografia.path):
                    elements.append(Spacer(1, 8))
                    elements.append(Paragraph("<b>FOTOGRAFÍA DEL LEVANTAMIENTO</b>", subtitle_style))
                    try:
                        # Imagen más pequeña para que quepa en la página
                        img = Image(levantamiento.fotografia.path, width=3.0*inch, height=2.0*inch)  # Reducido de 3.5x2.5
                        img.hAlign = 'CENTER'
                        elements.append(img)
                    except Exception as e:
                        elements.append(Paragraph("No se pudo cargar la imagen del levantamiento.", desc_style))
                
                # Comentario del revisor si existe
                if levantamiento.estado == 'Rechazado' and levantamiento.comentario_revisor:
                    elements.append(Spacer(1, 6))
                    comentario_style = ParagraphStyle(
                        'Comentario',
                        parent=desc_style,
                        backColor=colors.HexColor('#fff3f3'),
                        borderWidth=1,
                        borderColor=colors.HexColor('#ffcccc'),
                        borderPadding=6,
                        fontSize=8,
                        leading=10
                    )
                    elements.append(Paragraph(f"<b>COMENTARIO DEL REVISOR:</b> {levantamiento.comentario_revisor}", comentario_style))
            
            # Pie de página más compacto
            elements.append(Spacer(1, 8))  # Reducido de 16
            footer_style = ParagraphStyle(
                'Footer',
                parent=self.styles['Normal'],
                fontSize=6,  # Reducido de 7
                textColor=colors.HexColor('#666666'),
                alignment=2,
                spaceBefore=5  # Reducido de 10
            )
            
            # Texto más compacto
            footer_text = (
                f"{timezone.now().strftime('%d/%m/%Y %H:%M')} • "
                f"Por: {observacion.creado_por.get_full_name() if observacion.creado_por else 'Sistema'}"
            )
            elements.append(Paragraph(footer_text, footer_style))
            
            # Construir el PDF
            doc.build(elements)
            
            # Obtener el valor del buffer
            pdf = self.buffer.getvalue()
            self.buffer.close()
            
            return pdf
            
        except Exception as e:
            print(f"Error al generar el PDF: {str(e)}")
            raise


class ObservacionSSOMAGenerator(ObservacionPDFGenerator):
    """
    Generador de PDF para observaciones de seguridad SSOMA.
    Hereda de ObservacionPDFGenerator y adapta el contenido para las observaciones SSOMA.
    """
    
    def generate_pdf(self, observacion):
        """
        Genera el PDF con los detalles de la observación SSOMA en una sola página.
        """
        try:
            # Crear el documento PDF
            doc = SimpleDocTemplate(
                self.buffer,
                pagesize=letter,
                rightMargin=36,
                leftMargin=36,
                topMargin=36,
                bottomMargin=36
            )
            
            # Lista de elementos para el PDF
            elements = []
            
            # Crear el encabezado
            self._create_header(elements, observacion)
            
            # Estilos para el contenido
            subtitle_style = ParagraphStyle(
                'Subtitle',
                parent=self.styles['Subtitle'],
                fontSize=10,
                leading=12,
                spaceBefore=10,
                spaceAfter=4
            )
            
            desc_style = ParagraphStyle(
                'Description',
                parent=self.styles['Normal'],
                fontSize=9,
                leading=11,
                spaceBefore=0,
                spaceAfter=6
            )
            
            # Datos de la observación SSOMA
            data = [
                ["Ítem:", observacion.item],
                ["Fecha:", observacion.fecha.strftime('%d/%m/%Y')],
                ["Semana:", observacion.semana_obs],
                ["Punto de Inspección:", observacion.get_punto_inspeccion_display()],
                ["Subclasificación:", observacion.get_subclasificacion_display()],
                ["Tipo de Observación:", observacion.get_tipo_observacion_display()],
                ["Área:", observacion.get_area_display()],
                ["Nivel de Riesgo:", observacion.get_nivel_riesgo_display()],
                ["Estado:", observacion.get_estado_display()],
                ["Asignado a:", observacion.asignado_a.get_full_name() if observacion.asignado_a else 'No asignado'],
                ["Fecha Compromiso:", observacion.fecha_compromiso.strftime('%d/%m/%Y') if observacion.fecha_compromiso else 'No especificada'],
            ]
            
            # Tabla de datos
            table = Table(data, colWidths=['30%', '70%'])
            table.setStyle(TableStyle([
                ('FONT', (0, 0), (-1, -1), self.font_name, 9),
                ('FONT', (0, 0), (0, -1), self.bold_font_name, 9),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dddddd')),
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f5f5f5')),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            
            elements.append(table)
            
            # Descripción de la observación
            if observacion.descripcion:
                elements.append(Spacer(1, 10))
                elements.append(Paragraph("<b>DESCRIPCIÓN DE LA OBSERVACIÓN</b>", subtitle_style))
                elements.append(Paragraph(observacion.descripcion, desc_style))
            
            # Acción correctiva / Recomendación
            if observacion.accion_correctiva:
                elements.append(Spacer(1, 10))
                elements.append(Paragraph("<b>RECOMENDACIÓN Y ESTADO</b>", subtitle_style))
                elements.append(Paragraph(observacion.accion_correctiva, desc_style))
            
            # Sección de fotos
            self._create_photos_section(elements, observacion)
            
            # Pie de página
            elements.append(Spacer(1, 8))
            footer_style = ParagraphStyle(
                'Footer',
                parent=self.styles['Normal'],
                fontSize=6,
                textColor=colors.HexColor('#666666'),
                alignment=2,
                spaceBefore=5
            )
            
            footer_text = (
                f"{timezone.now().strftime('%d/%m/%Y %H:%M')} • "
                f"Por: {observacion.creado_por.get_full_name() if observacion.creado_por else 'Sistema'}"
            )
            elements.append(Paragraph(footer_text, footer_style))
            
            # Construir el PDF
            doc.build(elements)
            
            # Obtener el valor del buffer
            pdf = self.buffer.getvalue()
            self.buffer.close()
            
            return pdf
            
        except Exception as e:
            print(f"Error al generar el PDF SSOMA: {str(e)}")
            raise
