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
        # Estilo Normal
        if 'Normal' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='Normal',
                fontName=self.font_name,
                fontSize=10,
                leading=12,
                textColor=colors.black
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
                textColor=colors.HexColor('#444444')
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
    
    def _create_description_section(self, elements, observacion):
        """Crea la sección de descripción de la observación."""
        elements.append(Paragraph("<b>DESCRIPCIÓN DE LA OBSERVACIÓN</b>", self.styles['Subtitle']))
        
        # Descripción
        if observacion.descripcion:
            elements.append(Paragraph(observacion.descripcion, self.styles['Normal']))
        else:
            elements.append(Paragraph("No se proporcionó descripción.", self.styles['Normal']))
        
        elements.append(Spacer(1, 10))
        
        # Recomendaciones
        elements.append(Paragraph("<b>RECOMENDACIONES</b>", self.styles['Subtitle']))
        
        if hasattr(observacion, 'recomendacion') and observacion.recomendacion:
            elements.append(Paragraph(observacion.recomendacion, self.styles['Normal']))
        else:
            elements.append(Paragraph("No se proporcionaron recomendaciones.", self.styles['Normal']))
        
        elements.append(Spacer(1, 10))
        
        return elements
    
    def _create_levantamiento_section(self, elements, observacion, tipo):
        """Crea la sección de levantamiento si existe."""
        if tipo == "SSOMA" and hasattr(observacion, 'levantamiento') and observacion.levantamiento:
            levantamiento = observacion.levantamiento
            elements.append(Paragraph("<b>LEVANTAMIENTO DE OBSERVACIÓN</b>", self.styles['Subtitle']))
            
            data = [
                ['Fecha de Levantamiento', levantamiento.fecha_levantamiento.strftime('%d/%m/%Y') if levantamiento.fecha_levantamiento else ''],
                ['Estado', levantamiento.estado],
                ['Tiempo de Levantamiento', f"{levantamiento.tiempo_levantamiento.days} días" if levantamiento.tiempo_levantamiento else ''],
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
        
        return elements
    
    def _create_image_section(self, elements, observacion):
        """Crea la sección de imágenes si existen."""
        # Verificar si hay fotos en la observación (foto_1 o foto_2)
        has_photos = (hasattr(observacion, 'foto_1') and observacion.foto_1) or \
                     (hasattr(observacion, 'foto_2') and observacion.foto_2)
        
        if has_photos:
            elements.append(Paragraph("<b>EVIDENCIAS FOTOGRÁFICAS</b>", self.styles['Subtitle']))
            elements.append(Spacer(1, 10))
            
            # Crear lista de fotos disponibles
            fotos = []
            if hasattr(observacion, 'foto_1') and observacion.foto_1:
                fotos.append({'imagen': observacion.foto_1, 'descripcion': 'Foto 1'})
            if hasattr(observacion, 'foto_2') and observacion.foto_2:
                fotos.append({'imagen': observacion.foto_2, 'descripcion': 'Foto 2'})
            
            # Procesar imágenes en grupos de 2 por fila
            for i in range(0, len(fotos), 2):
                # Crear una fila con hasta 2 imágenes
                row_data = []
                for j in range(2):
                    idx = i + j
                    if idx < len(fotos):
                        foto_info = fotos[idx]
                        try:
                            img_path = os.path.join(settings.MEDIA_ROOT, str(foto_info['imagen']))
                            if os.path.exists(img_path):
                                # Redimensionar imagen para que quepa en el PDF
                                pil_img = PILImage.open(img_path)
                                width, height = pil_img.size
                                max_width = self.page_width * 0.4
                                max_height = 3 * inch
                                
                                # Calcular proporciones para mantener aspecto
                                ratio = min(max_width / width, max_height / height)
                                new_width = width * ratio
                                new_height = height * ratio
                                
                                # Crear celda con imagen y descripción
                                img_obj = Image(img_path, width=new_width, height=new_height)
                                
                                # Descripción de la imagen
                                desc = foto_info['descripcion']
                                
                                # Crear contenido de la celda
                                cell_content = [[img_obj], [Paragraph(desc, self.styles['Normal'])]]
                                row_data.append(Table(cell_content, colWidths=[max_width]))
                            else:
                                row_data.append(Paragraph("Imagen no encontrada", self.styles['Normal']))
                        except Exception as e:
                            row_data.append(Paragraph(f"Error al procesar imagen: {str(e)}", self.styles['Normal']))
                    else:
                        # Espacio vacío si no hay suficientes imágenes
                        row_data.append("")
                
                # Crear tabla para la fila de imágenes
                img_row = Table([row_data], colWidths=[self.page_width * 0.45, self.page_width * 0.45])
                img_row.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('TOPPADDING', (0, 0), (-1, -1), 5),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ]))
                
                elements.append(img_row)
                elements.append(Spacer(1, 10))
        
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
            self._create_description_section(elements, observacion)
            
            # Agregar sección de levantamiento si existe
            self._create_levantamiento_section(elements, observacion, "SSOMA")
            
            # Agregar imágenes si existen
            self._create_image_section(elements, observacion)
            
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
            self._create_description_section(elements, observacion)
            
            # Agregar imágenes si existen
            self._create_image_section(elements, observacion)
            
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
