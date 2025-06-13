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

class ReportePDFGenerator:
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
    
    def _create_header(self, elements, reporte):
        """Crea el encabezado del PDF con el logo y la información del reporte."""
        # Logo
        logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'Logo-JLV2.png')
        if os.path.exists(logo_path):
            logo = Image(logo_path, width=80, height=40)
            logo.hAlign = 'CENTER'
            elements.append(logo)
            elements.append(Spacer(1, 5))
        
        # Título
        title = Paragraph(f"{reporte.tipo_formulario}", self.styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 5))
        
        # Información general
        data = [
            ["PROYECTO:", reporte.proyecto.nombre],
            ["CÓDIGO:", reporte.codigo_proyecto or 'N/A'],
            ["FECHA:", reporte.fecha_emision.strftime('%d/%m/%Y')],
            ["REPORTE N°:", reporte.reporte_numero],
            ["CLIENTE:", reporte.cliente or 'N/A'],
            ["CONTRATISTA:", reporte.contratista or 'N/A'],
            ["ELABORADO POR:", reporte.elaborado_por or ''],
            ["REVISADO POR:", reporte.revisado_por or '']
        ]
        
        table_style = [
            ('FONT', (0, 0), (-1, -1), self.font_name, 8),
            ('FONT', (0, 0), (0, -1), self.bold_font_name, 8),  # Primera columna en negrita
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#eeeeee')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#eeeeee')),
            ('PADDING', (0, 0), (-1, -1), 2),
            ('LEFTPADDING', (0, 0), (0, -1), 4),
            ('RIGHTPADDING', (-1, 0), (-1, -1), 4),
        ]
        
        table = Table(data, colWidths=['30%', '70%'])
        table.setStyle(TableStyle(table_style))
        elements.append(table)
        elements.append(Spacer(1, 12))
    
    def _create_photo_table(self, fotos, start_idx=0, max_photos=None):
        """Crea una cuadrícula de tarjetas para las fotos.
        - Primera página: 4 fotos (2x2)
        - Páginas siguientes: 6 fotos (3x2)
        """
        elements = []
        if not fotos:
            return elements
            
        # Limitar el número de fotos si se especifica
        if max_photos is not None:
            fotos = fotos[start_idx:start_idx + max_photos]
        else:
            fotos = fotos[start_idx:]
            
        # Siempre mostrar 4 fotos en la primera página (2x2)
        if start_idx == 0:
            fotos_por_pagina = 4
        else:  # Páginas siguientes
            fotos_por_pagina = 6  # 3x2
        
        # Tamaños fijos para la cuadrícula
        margen_pagina = 1.5 * cm  # 1.5cm de margen a cada lado
        ancho_util = self.page_width - (2 * margen_pagina)
        espacio_entre = 0.7 * cm  # Reducir espacio entre tarjetas
        
        # Determinar número de columnas
        if start_idx == 0:  # Primera página siempre 2 columnas (2x2)
            columnas = 2
        else:  # Páginas siguientes
            columnas = 3  # 3 columnas (3x2)
            
        # Tamaño de cada tarjeta
        ancho_tarjeta = (ancho_util - (espacio_entre * (columnas - 1))) / columnas
        alto_tarjeta = (self.page_height * 0.3)  # Reducir altura para más fotos
        
        # Tamaño de la imagen (un poco más pequeño que la tarjeta)
        ancho_imagen = ancho_tarjeta - 0.5 * cm  # Reducir el margen horizontal
        if start_idx == 0:  # Primera página siempre 4 fotos (2x2)
            alto_imagen = alto_tarjeta * 0.85  # Más espacio para imágenes
        else:  # Páginas siguientes
            alto_imagen = alto_tarjeta * 0.7  # Tamaño estándar para páginas siguientes
        
        # Estilos
        estilo_titulo = ParagraphStyle(
            'TituloFoto',
            fontName=self.bold_font_name,
            fontSize=10,
            leading=12,
            alignment=1,  # Centrado
            spaceAfter=5,
            textColor=colors.HexColor('#2c3e50'),
            backColor=colors.HexColor('#f8f9fa'),
            borderWidth=1,
            borderColor=colors.HexColor('#dee2e6'),
            borderRadius=3,
            padding=(5, 5, 5, 5)
        )
        
        estilo_descripcion = ParagraphStyle(
            'DescripcionFoto',
            fontName=self.font_name,
            fontSize=8,
            leading=10,
            alignment=1,  # Centrado
            spaceBefore=5,
            spaceAfter=5,
            textColor=colors.HexColor('#495057'),
            backColor=colors.white,
            borderWidth=1,
            borderColor=colors.HexColor('#e9ecef'),
            borderRadius=3,
            padding=(5, 5, 5, 5)
        )
        
        # Procesar las fotos en lotes según corresponda
        i = 0
        while i < len(fotos):
            # Si es la primera página y hay más de 4 fotos, mostrar solo 4
            if start_idx == 0 and len(fotos) > 4 and i == 0:
                fotos_a_mostrar = 4
            else:
                fotos_a_mostrar = min(fotos_por_pagina, len(fotos) - i)
            
            # Si no hay fotos para mostrar, salir
            if fotos_a_mostrar <= 0:
                break
                
            # Agregar salto de página si no es la primera página
            if i > 0:
                elements.append(PageBreak())
            
            # Título de la sección
            elements.append(Paragraph("FOTOGRAFÍAS", self.styles['Subtitle']))
            elements.append(Spacer(1, 15))  # Espacio después del título
            
            # Procesar las fotos de esta página
            fotos_pagina = fotos[i:i + fotos_a_mostrar]
            i += fotos_a_mostrar  # Actualizar el índice para la siguiente iteración
            
            # Crear tabla para la cuadrícula
            data = []
            
            # Primera fila (2 o 3 fotos dependiendo de la página)
            fila1 = []
            for j in range(min(columnas, len(fotos_pagina))):
                if j < len(fotos_pagina):
                    foto = fotos_pagina[j]
                    ruta_imagen = foto['imagen_path'].replace('file://', '')
                    
                    if os.path.exists(ruta_imagen):
                        try:
                            # Crear tarjeta sin título
                            contenido_tarjeta = [
                                # Fila de la imagen
                                [Image(ruta_imagen, width=ancho_imagen, height=alto_imagen, kind='proportional', hAlign='CENTER')],
                                # Espacio y descripción
                                [Spacer(1, 5)],  # Espacio entre imagen y descripción
                                [Paragraph(f"{foto.get('descripcion', '')}", estilo_descripcion)]
                            ]
                            
                            # Crear tabla para la tarjeta
                            tarjeta = Table(contenido_tarjeta, colWidths=ancho_tarjeta)
                            
                            # Estilo de la tarjeta
                            estilo_tarjeta = TableStyle([
                                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
                                ('BACKGROUND', (0, 0), (-1, -1), colors.white),
                                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                ('PADDING', (0, 0), (-1, -1), 6),  # Padding reducido
                                ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor('#e9ecef')),
                                ('LINEABOVE', (0, -1), (-1, -1), 1, colors.HexColor('#e9ecef')),
                            ])
                            
                            tarjeta.setStyle(estilo_tarjeta)
                            fila1.append(tarjeta)
                            
                        except Exception as e:
                            print(f"Error al procesar imagen {ruta_imagen}: {str(e)}")
                            fila1.append(Spacer(1, 1))
                    else:
                        fila1.append(Spacer(1, 1))
                else:
                    fila1.append(Spacer(1, 1))  # Celda vacía
            
            # Segunda fila (fotos restantes)
            fila2 = []
            start_j = columnas  # Comenzar después de la primera fila
            for j in range(start_j, start_j + columnas):
                if j < len(fotos_pagina):
                    foto = fotos_pagina[j]
                    ruta_imagen = foto['imagen_path'].replace('file://', '')
                    
                    if os.path.exists(ruta_imagen):
                        try:
                            # Crear tarjeta sin título
                            contenido_tarjeta = [
                                # Fila de la imagen
                                [Image(ruta_imagen, width=ancho_imagen, height=alto_imagen, kind='proportional', hAlign='CENTER')],
                                # Espacio y descripción
                                [Spacer(1, 5)],  # Espacio entre imagen y descripción
                                [Paragraph(f"{foto.get('descripcion', '')}", estilo_descripcion)]
                            ]
                            
                            # Crear tabla para la tarjeta
                            tarjeta = Table(contenido_tarjeta, colWidths=ancho_tarjeta)
                            
                            # Estilo de la tarjeta
                            estilo_tarjeta = TableStyle([
                                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
                                ('BACKGROUND', (0, 0), (-1, -1), colors.white),
                                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                ('PADDING', (0, 0), (-1, -1), 6),  # Padding reducido
                                ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor('#e9ecef')),
                                ('LINEABOVE', (0, -1), (-1, -1), 1, colors.HexColor('#e9ecef')),
                            ])
                            
                            tarjeta.setStyle(estilo_tarjeta)
                            fila2.append(tarjeta)
                            
                        except Exception as e:
                            print(f"Error al procesar imagen {ruta_imagen}: {str(e)}")
                            fila2.append(Spacer(1, 1))
                    else:
                        fila2.append(Spacer(1, 1))
                else:
                    fila2.append(Spacer(1, 1))  # Celda vacía
            
            # Asegurar que siempre haya el número correcto de celdas en cada fila
            while len(fila1) < columnas:
                fila1.append(Spacer(1, 1))
            while len(fila2) < columnas:
                fila2.append(Spacer(1, 1))
            
            # Crear la tabla principal con las dos filas de tarjetas
            tabla = Table(
                [fila1, [Spacer(1, 0.3 * cm)], fila2],  # Espacio reducido entre filas
                colWidths=[ancho_tarjeta] * columnas,
                rowHeights=[alto_tarjeta, 0.3 * cm, alto_tarjeta]
            )
            
            # Estilo de la tabla principal
            estilo_tabla = TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('PADDING', (0, 0), (-1, -1), 5),
                ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ])
            
            tabla.setStyle(estilo_tabla)
            elements.append(tabla)
        
        return elements
    
    def generate_pdf(self, reporte, fotos):
        """Genera el PDF con los detalles del reporte."""
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
            
            # Agregar encabezado con información del reporte
            self._create_header(elements, reporte)
            
            # Agregar descripción del reporte si existe
            if reporte.descripcion:
                elements.append(Paragraph("<b>DESCRIPCIÓN</b>", self.styles['Subtitle']))
                elements.append(Paragraph(reporte.descripcion, self.styles['Normal']))
                elements.append(Spacer(1, 12))
            
            # Agregar sección de fotos
            photo_elements = self._create_photo_table(fotos)
            elements.extend(photo_elements)
            
            # Espacio después de las fotos
            elements.append(Spacer(1, 10))
            
            # Construir el PDF
            doc.build(elements)
            
            # Obtener el PDF generado
            pdf = self.buffer.getvalue()
            self.buffer.close()
            
            return pdf
            
        except Exception as e:
            # En caso de error, registrar y relanzar
            print(f"Error al generar PDF: {str(e)}")
            raise
