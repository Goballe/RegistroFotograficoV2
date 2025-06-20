import os
from io import BytesIO
from django.conf import settings
from django.utils import timezone
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
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
        # Usaremos directamente la fuente GOTHIC.TTF que sabemos que existe en el sistema
        try:
            # Registrar Century Gothic
            pdfmetrics.registerFont(TTFont('CenturyGothic', 'C:/Windows/Fonts/GOTHIC.TTF'))
            pdfmetrics.registerFont(TTFont('CenturyGothic-Bold', 'C:/Windows/Fonts/GOTHICB.TTF'))
            self.font_name = 'CenturyGothic'
            self.bold_font_name = 'CenturyGothic-Bold'
            print("Century Gothic registrada correctamente")
        except Exception as e:
            print(f"Error al cargar Century Gothic: {str(e)}")
            # Si falla, usar Arial como respaldo
            try:
                pdfmetrics.registerFont(TTFont('Arial', 'C:/Windows/Fonts/arial.ttf'))
                pdfmetrics.registerFont(TTFont('Arial-Bold', 'C:/Windows/Fonts/arialbd.ttf'))
                self.font_name = 'Arial'
                self.bold_font_name = 'Arial-Bold'
                print("Usando Arial como respaldo")
            except Exception as e2:
                print(f"Error al cargar Arial: {str(e2)}")
                # Si todo falla, usar fuentes estándar
                self.font_name = 'Helvetica'
                self.bold_font_name = 'Helvetica-Bold'
                print("Usando Helvetica como respaldo final")
    
    def _register_custom_styles(self):
        """Registra estilos personalizados para el PDF."""
        # Estilo Normal
        if 'Normal' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='Normal',
                fontName=self.font_name,
                fontSize=10,
                leading=12,
                textColor=colors.black,
                alignment=0,  # Izquierda
                leftIndent=15  # Indentación izquierda para mejor alineación
            ))
        
        # Estilo Título
        if 'Title' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='Title',
                fontName=self.bold_font_name,
                fontSize=16,
                leading=18,
                alignment=1,  # Centrado
                spaceAfter=12,
                textColor=colors.HexColor('#333333')
            ))
        
        # Estilo Subtítulo
        if 'Subtitle' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='Subtitle',
                fontName=self.bold_font_name,
                fontSize=12,
                leading=14,
                spaceAfter=8,
                textColor=colors.HexColor('#444444'),
                alignment=0,  # Izquierda
                leftIndent=15  # Indentación izquierda para mejor alineación
            ))
        
        # Estilo Encabezado
        if 'Header' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='Header',
                fontName=self.bold_font_name,
                fontSize=10,
                leading=12,
                textColor=colors.white,
                backColor=colors.HexColor('#92263f'),
                alignment=1,  # Centrado
                padding=4,
                spaceAfter=8
            ))
    
    def _create_header(self, elements, observacion, tipo):
        """Crea el encabezado del PDF con el logo y la información de la observación."""
        # Logo
        logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'Logo-JLV2.png')
        if os.path.exists(logo_path):
            logo = Image(logo_path, width=80, height=40)
            logo.hAlign = 'CENTER'
            elements.append(logo)
            elements.append(Spacer(1, 5))
        
        # Título
        title = Paragraph(f"OBSERVACIÓN DE {tipo}", self.styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 5))
        
        # Información general
        data = [
            ['Proyecto', observacion.proyecto.nombre],
            ['Item', observacion.item],
            ['Fecha', observacion.fecha.strftime('%d/%m/%Y') if observacion.fecha else ''],
            ['Semana', observacion.semana_obs],
            ['Estado', observacion.estado],
        ]
        
        # Agregar campos específicos según el tipo de observación
        if tipo == "SSOMA":
            data.extend([
                ['Nivel de Riesgo', observacion.nivel_riesgo],
                ['Punto de Inspección', observacion.punto_inspeccion],
                ['Subclasificación', observacion.subclasificacion],
            ])
        elif tipo == "CALIDAD":
            data.extend([
                ['Punto de Inspección', observacion.punto_inspeccion],
                ['Sub Clasificación', observacion.sub_clasificacion],
                ['Nivel de Riesgo', observacion.nivel_riesgo],
            ])
        
        # Tabla de información
        info_table = Table(data, colWidths=[self.page_width * 0.2, self.page_width * 0.7])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f2f2f2')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#333333')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), self.bold_font_name),
            ('FONTNAME', (1, 0), (-1, -1), self.font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dddddd')),
        ]))
        
        elements.append(info_table)
        elements.append(Spacer(1, 10))
        
        return elements
    
    def _create_description_section(self, elements, observacion, tipo):
        """Crea la sección de descripción de la observación."""
        elements.append(Paragraph("<b>DESCRIPCIÓN DE LA OBSERVACIÓN</b>", self.styles['Subtitle']))
        
        # Crear estilo para la descripción con indentación
        desc_style = ParagraphStyle(
            'DescriptionStyle',
            parent=self.styles['Normal'],
            leftIndent=20,  # Indentación izquierda
            firstLineIndent=0,
            spaceBefore=5,
            spaceAfter=5
        )
        
        # Crear párrafo para la descripción con el nuevo estilo
        descripcion_text = observacion.descripcion if observacion.descripcion else "No hay descripción disponible."
        elements.append(Paragraph(descripcion_text, desc_style))
        elements.append(Spacer(1, 10))
        
        # Agregar acción correctiva si es una observación SSOMA
        if tipo == 'ssoma' and hasattr(observacion, 'accion_correctiva') and observacion.accion_correctiva:
            elements.append(Paragraph("<b>ACCIÓN CORRECTIVA PROPUESTA</b>", self.styles['Subtitle']))
            elements.append(Paragraph(observacion.accion_correctiva, desc_style))  # Usar el mismo estilo con indentación
            elements.append(Spacer(1, 10))
        
        # Agregar recomendación si es una observación de Calidad
        if tipo == 'calidad' and hasattr(observacion, 'recomendacion') and observacion.recomendacion:
            elements.append(Paragraph("<b>RECOMENDACIÓN</b>", self.styles['Subtitle']))
            elements.append(Paragraph(observacion.recomendacion, desc_style))  # Usar el mismo estilo con indentación
            elements.append(Spacer(1, 10))
        
        return elements
    
    def _create_levantamiento_section(self, elements, observacion, tipo):
        """Crea la sección de levantamiento si existe."""
        if hasattr(observacion, 'levantamiento') and observacion.levantamiento:
            levantamiento = observacion.levantamiento
            elements.append(Paragraph("<b>LEVANTAMIENTO DE OBSERVACIÓN</b>", self.styles['Subtitle']))
            
            # Estilo para el contenido del levantamiento con indentación adicional
            lev_style = ParagraphStyle(
                'LevantamientoStyle',
                parent=self.styles['Normal'],
                leftIndent=20,  # Indentación adicional
                firstLineIndent=0
            )
            
            data = [
                ['Fecha de Levantamiento', levantamiento.fecha_levantamiento.strftime('%d/%m/%Y') if levantamiento.fecha_levantamiento else ''],
                ['Estado', levantamiento.estado],
                ['Tiempo de Levantamiento', levantamiento.tiempo_levantamiento if levantamiento.tiempo_levantamiento else ''],
                ['Descripción', levantamiento.descripcion or ''],
            ]
            
            if levantamiento.comentario_revisor:
                data.append(['Comentario del Revisor', levantamiento.comentario_revisor])
            
            # Tabla de levantamiento
            levantamiento_table = Table(data, colWidths=[self.page_width * 0.3, self.page_width * 0.6])
            levantamiento_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f2f2f2')),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#333333')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), self.bold_font_name),
                ('FONTNAME', (1, 0), (-1, -1), self.font_name),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dddddd')),
            ]))
            
            elements.append(levantamiento_table)
            elements.append(Spacer(1, 10))
            
            # Agregar fotografía del levantamiento si existe
            if hasattr(levantamiento, 'fotografia') and levantamiento.fotografia:
                elements.append(Paragraph("<b>EVIDENCIAS FOTOGRÁFICAS DEL LEVANTAMIENTO</b>", self.styles['Subtitle']))
                elements.append(Spacer(1, 10))
                
                try:
                    img_path = os.path.join(settings.MEDIA_ROOT, str(levantamiento.fotografia))
                    if os.path.exists(img_path):
                        # Redimensionar imagen para que quepa en el PDF
                        pil_img = PILImage.open(img_path)
                        width, height = pil_img.size
                        max_width = self.page_width * 0.45  # Imagen más pequeña
                        max_height = 2.5 * inch
                        
                        # Calcular proporciones para mantener aspecto
                        ratio = min(max_width / width, max_height / height)
                        new_width = width * ratio
                        new_height = height * ratio
                        
                        # Crear imagen
                        img_obj = Image(img_path, width=new_width, height=new_height)
                        img_obj.hAlign = 'CENTER'  # Centrar la imagen
                        
                        # Añadir imagen al PDF
                        elements.append(img_obj)
                        elements.append(Spacer(1, 10))
                    else:
                        elements.append(Paragraph("Imagen del levantamiento no encontrada", self.styles['Normal']))
                except Exception as e:
                    elements.append(Paragraph(f"Error al procesar imagen del levantamiento: {str(e)}", self.styles['Normal']))
        
        return elements
    
    def _create_image_section(self, elements, observacion):
        """Crea la sección de imágenes si existen."""
        # Verificar si hay fotos en la observación (foto_1 o foto_2)
        has_photos = (hasattr(observacion, 'foto_1') and observacion.foto_1) or \
                     (hasattr(observacion, 'foto_2') and observacion.foto_2)
        
        if has_photos:
            elements.append(Paragraph("<b>EVIDENCIAS FOTOGRÁFICAS</b>", self.styles['Subtitle']))
            elements.append(Spacer(1, 10))
            
            # Crear lista de fotos disponibles en orden
            fotos = []
            if hasattr(observacion, 'foto_1') and observacion.foto_1:
                fotos.append({'imagen': observacion.foto_1})
            if hasattr(observacion, 'foto_2') and observacion.foto_2:
                fotos.append({'imagen': observacion.foto_2})
            
            # Si tenemos fotos, las mostramos en una sola fila
            if fotos:
                # Preparar las imágenes para la tabla
                row_data = []
                
                for foto_info in fotos:
                    try:
                        img_path = os.path.join(settings.MEDIA_ROOT, str(foto_info['imagen']))
                        if os.path.exists(img_path):
                            # Redimensionar imagen para que quepa en el PDF
                            pil_img = PILImage.open(img_path)
                            width, height = pil_img.size
                            max_width = self.page_width * 0.4  # Ajustar para que quepan dos en una fila
                            max_height = 2.5 * inch
                            
                            # Calcular proporciones para mantener aspecto
                            ratio = min(max_width / width, max_height / height)
                            new_width = width * ratio
                            new_height = height * ratio
                            
                            # Crear imagen
                            img_obj = Image(img_path, width=new_width, height=new_height)
                            row_data.append(img_obj)
                        else:
                            # Espacio vacío si no se encuentra la imagen
                            row_data.append("")
                    except Exception as e:
                        # Espacio vacío en caso de error
                        row_data.append("")
                
                # Si solo hay una foto, añadir un espacio vacío para mantener la estructura
                if len(row_data) == 1:
                    row_data.append("")
                
                # Crear tabla con las imágenes en una fila
                img_table = Table([row_data], colWidths=[self.page_width * 0.45, self.page_width * 0.45])
                img_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))
                
                elements.append(img_table)
                elements.append(Spacer(1, 15))
        
        return elements
    
    def generate_pdf_ssoma(self, observacion):
        """Genera el PDF para una observación SSOMA."""
        try:
            # Configurar el documento con márgenes mínimos
            doc = SimpleDocTemplate(
                self.buffer,
                pagesize=letter,
                rightMargin=15,
                leftMargin=15,
                topMargin=20,
                bottomMargin=15
            )
            
            elements = []
            
            # Agregar encabezado con información de la observación
            self._create_header(elements, observacion, "SSOMA")
            
            # Agregar descripción y acciones correctivas
            self._create_description_section(elements, observacion, "ssoma")
            
            # Agregar imágenes de la observación si existen
            self._create_image_section(elements, observacion)
            
            # Agregar salto de página antes del levantamiento
            elements.append(PageBreak())
            
            # Agregar sección de levantamiento si existe
            self._create_levantamiento_section(elements, observacion, "SSOMA")
            
            # Construir el PDF
            doc.build(elements)
            
            # Obtener el PDF generado
            pdf = self.buffer.getvalue()
            self.buffer.close()
            
            return pdf
            
        except Exception as e:
            # En caso de error, registrar y relanzar
            print(f"Error al generar PDF SSOMA: {str(e)}")
            raise
    
    def generate_pdf_calidad(self, observacion):
        """Genera el PDF para una observación de Calidad."""
        try:
            # Configurar el documento con márgenes mínimos
            doc = SimpleDocTemplate(
                self.buffer,
                pagesize=letter,
                rightMargin=15,
                leftMargin=15,
                topMargin=20,
                bottomMargin=15
            )
            
            elements = []
            
            # Agregar encabezado con información de la observación
            self._create_header(elements, observacion, "CALIDAD")
            
            # Agregar descripción y acciones correctivas
            self._create_description_section(elements, observacion, "calidad")
            
            # Agregar imágenes de la observación si existen
            self._create_image_section(elements, observacion)
            
            # Agregar salto de página antes del levantamiento
            elements.append(PageBreak())
            
            # Agregar sección de levantamiento si existe
            self._create_levantamiento_section(elements, observacion, "CALIDAD")
            
            # Construir el PDF
            doc.build(elements)
            
            # Obtener el PDF generado
            pdf = self.buffer.getvalue()
            self.buffer.close()
            
            return pdf
            
        except Exception as e:
            # En caso de error, registrar y relanzar
            print(f"Error al generar PDF Calidad: {str(e)}")
            raise
