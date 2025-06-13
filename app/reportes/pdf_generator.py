import os
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.units import cm, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from django.conf import settings

def register_fonts():
    """Registra fuentes personalizadas si están disponibles"""
    try:
        # Intentar registrar Arial si está disponible
        font_path = os.path.join(settings.BASE_DIR, 'static', 'fonts', 'arial.ttf')
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont('Arial', font_path))
            pdfmetrics.registerFont(TTFont('Arial-Bold', font_path))
    except:
        pass  # Usar fuentes por defecto si hay algún error

class ReportePDFGenerator:
    def __init__(self, buffer, page_size=letter):
        self.buffer = buffer
        self.page_width, self.page_height = page_size
        self.styles = getSampleStyleSheet()
        
        # Registrar fuentes
        register_fonts()
        
        # Definir estilos personalizados
        self._define_styles()
    
    def _define_styles(self):
        """Define los estilos de párrafo personalizados"""
        # Verificar y definir solo los estilos que no existen
        if 'Title' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='Title',
                parent=self.styles['Heading1'],
                fontSize=16,
                leading=18,
                alignment=1,  # 0=izq, 1=centro, 2=derecha
                spaceAfter=20,
                fontName='Helvetica-Bold'
            ))
        
        if 'Section' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='Section',
                parent=self.styles['Heading2'],
                fontSize=12,
                leading=14,
                spaceAfter=10,
                fontName='Helvetica-Bold'
            ))
        
        if 'Normal' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='Normal',
                parent=self.styles['Normal'],
                fontSize=10,
                leading=12
            ))
        
        if 'Small' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='Small',
                parent=self.styles['Normal'],
                fontSize=8,
                leading=10
            ))
    
    def _draw_header(self, canvas, doc, reporte):
        """Dibuja el encabezado del reporte"""
        # Configuración inicial
        canvas.saveState()
        
        # Configuración de fuentes
        title_font = ('Helvetica-Bold', 16)
        header_font = ('Helvetica-Bold', 10)
        text_font = ('Helvetica', 9)
        
        # Título centrado
        canvas.setFont(*title_font)
        canvas.drawCentredString(self.page_width / 2.0, self.page_height - 2.5*cm, "REPORTE FOTOGRÁFICO")
        
        # Posiciones iniciales
        y_position = self.page_height - 4.0*cm
        line_height = 0.5*cm
        col1_x = 2.5*cm
        col2_x = 10.5*cm
        
        # Establecer fuente para el texto
        canvas.setFont(*text_font)
        
        # Columna izquierda - Títulos
        canvas.setFont(*header_font)
        canvas.drawString(col1_x, y_position, "PROYECTO:")
        canvas.drawString(col1_x, y_position - line_height, "FECHA:")
        canvas.drawString(col1_x, y_position - 2*line_height, "REPORTE N°:")
        
        # Columna derecha - Títulos
        canvas.drawString(col2_x, y_position, "CÓDIGO:")
        canvas.drawString(col2_x, y_position - line_height, "CLIENTE:")
        canvas.drawString(col2_x, y_position - 2*line_height, "CONTRATISTA:")
        
        # Columna izquierda - Valores
        canvas.setFont(*text_font)
        canvas.drawString(col1_x + 2.2*cm, y_position, f"{reporte.proyecto.nombre}")
        canvas.drawString(col1_x + 2.2*cm, y_position - line_height, f"{reporte.fecha_emision.strftime('%d/%m/%Y')}")
        canvas.drawString(col1_x + 2.2*cm, y_position - 2*line_height, f"{reporte.reporte_numero}")
        
        # Columna derecha - Valores
        canvas.drawString(col2_x + 1.8*cm, y_position, f"{reporte.codigo_proyecto or 'N/A'}")
        canvas.drawString(col2_x + 1.8*cm, y_position - line_height, f"{reporte.cliente or 'N/A'}")
        canvas.drawString(col2_x + 1.8*cm, y_position - 2*line_height, f"{reporte.contratista or 'N/A'}")
        
        # Línea separadora
        canvas.setLineWidth(0.5)
        canvas.line(2*cm, self.page_height - 6.2*cm, self.page_width - 2*cm, self.page_height - 6.2*cm)
        
        # Ajustar el margen superior para el contenido principal
        doc.topMargin = 7*cm
        canvas.restoreState()
    
    def _create_photo_table(self, fotos, start_idx=0, max_photos=None):
        """Crea una tabla con las fotos y sus descripciones"""
        elements = []
        
        # Filtrar solo las fotos que existen
        valid_fotos = []
        for foto in fotos:
            img_path = foto['imagen_path'].replace('file://', '')
            if os.path.exists(img_path):
                valid_fotos.append(foto)
        
        # Si se especifica un máximo de fotos, limitar
        if max_photos is not None:
            valid_fotos = valid_fotos[start_idx:start_idx + max_photos]
        else:
            valid_fotos = valid_fotos[start_idx:]
        
        # Crear una tabla con 2 columnas
        data = []
        row = []
        
        for i, foto in enumerate(valid_fotos, start_idx + 1):
            img_path = foto['imagen_path'].replace('file://', '')
            
            # Crear el contenido de la celda
            cell_content = [
                # Número de foto en la esquina superior izquierda
                Paragraph(
                    f"<b>{i}</b>", 
                    style=ParagraphStyle(
                        name=f'PhotoNumber_{i}',
                        fontName='Helvetica-Bold',
                        fontSize=10,
                        leading=12,
                        textColor=colors.black,
                        leftIndent=0.2*cm,
                        spaceBefore=0.1*cm
                    )
                ),
                # Imagen centrada con borde
                self._create_image(img_path, width=7.5*cm, height=5.5*cm),
                # Descripción centrada debajo de la imagen
                Paragraph(
                    f"{foto.get('descripcion', '')}",
                    style=ParagraphStyle(
                        name=f'PhotoDesc_{i}',
                        fontName='Helvetica',
                        fontSize=9,
                        leading=10,
                        alignment=1,  # Centrado
                        spaceBefore=0.2*cm,
                        textColor=colors.black
                    )
                )
            ]
            
            # Crear la celda con borde
            cell = Table([cell_content], colWidths=[8*cm])
            cell.setStyle(TableStyle([
                ('BOX', (0, 0), (-1, -1), 0.5, colors.black),  # Borde exterior
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('PADDING', (0, 0), (-1, -1), 0.2*cm),
                ('LEFTPADDING', (0, 0), (-1, -1), 0.2*cm),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0.2*cm),
                ('TOPPADDING', (0, 0), (-1, -1), 0.2*cm),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0.4*cm),
                ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ]))
            
            # Añadir celda a la fila
            row.append(cell)
            
            # Si tenemos 2 columnas, añadir la fila a los datos y reiniciar
            if len(row) == 2:
                data.append(row)
                row = []
        
        # Añadir la última fila si queda incompleta
        if row:
            data.append(row)
        
        # Crear la tabla principal con espaciado
        if data:
            table = Table(data, colWidths=[9*cm, 9*cm])
            table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0.5*cm),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0.5*cm),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 1*cm),
                ('TOPPADDING', (0, 0), (-1, -1), 0.5*cm)
            ]))
            elements.append(Spacer(1, 0.5*cm))  # Espacio antes de la tabla
            elements.append(table)
        
        return elements, len(valid_fotos)
    
    def _create_image(self, path, width, height):
        """Crea un elemento de imagen con tamaño fijo"""
        try:
            return Image(path, width=width, height=height, kind='proportional')
        except:
            # En caso de error al cargar la imagen, mostrar un recuadro con mensaje
            from reportlab.platypus.flowables import XBox
            return XBox(width, height, 'Imagen no disponible')
    
    def generate_pdf(self, reporte, fotos):
        """Genera el PDF completo con paginación"""
        # Configurar el documento
        doc = SimpleDocTemplate(
            self.buffer,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm,
            pagesize=letter
        )
        
        # Filtrar solo las fotos que existen
        valid_fotos = []
        for foto in fotos:
            img_path = foto['imagen_path'].replace('file://', '')
            if os.path.exists(img_path):
                valid_fotos.append(foto)
        
        # Calcular cuántas páginas necesitamos (4 fotos por página)
        fotos_por_pagina = 4
        total_fotos = len(valid_fotos)
        total_paginas = (total_fotos + fotos_por_pagina - 1) // fotos_por_pagina
        
        # Elementos del documento
        elements = []
        
        # Procesar las fotos por páginas
        for pagina in range(total_paginas):
            # Si no es la primera página, agregar un salto de página
            if pagina > 0:
                elements.append(PageBreak())
            
            # Calcular índices de fotos para esta página
            inicio = pagina * fotos_por_pagina
            fin = min(inicio + fotos_por_pagina, total_fotos)
            
            # Agregar título de sección con número de página
            elements.append(Paragraph(
                f"<b>FOTOGRAFÍAS ({pagina + 1}/{total_paginas})</b>",
                style=ParagraphStyle(
                    name=f'SectionTitle_{pagina}',
                    fontName='Helvetica-Bold',
                    fontSize=12,
                    spaceAfter=12,
                    alignment=1  # Centrado
                )
            ))
            
            # Agregar fotos de esta página
            photo_table, _ = self._create_photo_table(valid_fotos, inicio, fin - inicio)
            elements.extend(photo_table)
        
        # Construir el PDF
        doc.build(
            elements,
            onFirstPage=lambda c, d: self._draw_header(c, d, reporte),
            onLaterPages=lambda c, d: self._draw_header(c, d, reporte),
        )
        
        # Obtener el valor del buffer y devolverlo
        pdf = self.buffer.getvalue()
        self.buffer.close()
        return pdf
