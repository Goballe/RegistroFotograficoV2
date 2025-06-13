import pandas as pd
from io import BytesIO
from django.http import HttpResponse
from django.utils import timezone


def export_observaciones_calidad_to_excel(observaciones):
    """
    Exporta las observaciones de calidad a un archivo Excel.
    """
    # Crear un DataFrame con los datos de las observaciones
    data = []
    for obs in observaciones:
        # Informacion general de la observacion
        row = {
            'Item': obs.item,
            'Fecha': obs.fecha.strftime('%d/%m/%Y') if obs.fecha else '',
            'Semana': obs.semana_obs,
            'Punto de Inspeccion': obs.get_punto_inspeccion_display(),
            'Sub Clasificacion': obs.get_sub_clasificacion_display(),
            'Descripcion': obs.descripcion,
            'Nivel de Riesgo': obs.get_nivel_riesgo_display(),
            'Recomendacion': obs.recomendacion,
            'Estado': obs.get_estado_display(),
            'Asignado a': str(obs.asignado_a) if obs.asignado_a else 'No asignado',
            'Creado por': str(obs.creado_por) if obs.creado_por else 'Desconocido',
            'Creado en': obs.creado_en.strftime('%d/%m/%Y %H:%M') if obs.creado_en else '',
            'Actualizado en': obs.actualizado_en.strftime('%d/%m/%Y %H:%M') if obs.actualizado_en else '',
            'Fotos': 'Si' if obs.foto_1 or obs.foto_2 else 'No',
        }
        
        # Informacion del levantamiento si existe
        if hasattr(obs, 'levantamiento') and obs.levantamiento:
            lev = obs.levantamiento
            row.update({
                'Levantamiento - Estado': lev.get_estado_display(),
                'Levantamiento - Fecha': lev.fecha_levantamiento.strftime('%d/%m/%Y') if lev.fecha_levantamiento else '',
                'Levantamiento - Tiempo': lev.tiempo_levantamiento if lev.tiempo_levantamiento else '',
                'Levantamiento - Descripcion': lev.descripcion,
                'Levantamiento - Revisado por': str(lev.revisor) if lev.revisor else 'No revisado',
                'Levantamiento - Revisado en': lev.revisado_en.strftime('%d/%m/%Y %H:%M') if lev.revisado_en else '',
                'Levantamiento - Comentario revisor': lev.comentario_revisor if lev.comentario_revisor else '',
            })
        else:
            row.update({
                'Levantamiento - Estado': 'Sin levantamiento',
                'Levantamiento - Fecha': '',
                'Levantamiento - Tiempo': '',
                'Levantamiento - Descripcion': '',
                'Levantamiento - Revisado por': '',
                'Levantamiento - Revisado en': '',
                'Levantamiento - Comentario revisor': '',
            })
        
        data.append(row)
    
    # Crear el DataFrame
    df = pd.DataFrame(data)
    
    # Crear el archivo Excel en memoria
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Observaciones Calidad', index=False)
        worksheet = writer.sheets['Observaciones Calidad']
        
        # Ajustar el ancho de las columnas
        for i, col in enumerate(df.columns):
            max_length = max(
                df[col].astype(str).map(len).max(),
                len(col)
            ) + 2
            worksheet.column_dimensions[chr(65 + i)].width = min(max_length, 50)
    
    # Preparar la respuesta HTTP
    output.seek(0)
    filename = f'observaciones_calidad_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename={filename}'
    
    return response


def export_observaciones_ssoma_to_excel(observaciones):
    """
    Exporta las observaciones de SSOMA a un archivo Excel.
    """
    # Crear un DataFrame con los datos de las observaciones
    data = []
    for obs in observaciones:
        # Informacion general de la observacion
        row = {
            'Item': obs.item,
            'Fecha': obs.fecha.strftime('%d/%m/%Y') if obs.fecha else '',
            'Semana': obs.semana_obs,
            'Punto de Inspeccion': obs.get_punto_inspeccion_display(),
            'Subclasificacion': obs.get_subclasificacion_display(),
            'Descripcion': obs.descripcion,
            'Accion Correctiva': obs.accion_correctiva,
            'Nivel de Riesgo': obs.get_nivel_riesgo_display(),
            'Fecha de Compromiso': obs.fecha_compromiso.strftime('%d/%m/%Y') if obs.fecha_compromiso else '',
            'Estado': obs.get_estado_display(),
            'Responsable': str(obs.asignado_a) if obs.asignado_a else 'No asignado',
            'Creado por': str(obs.creado_por) if obs.creado_por else 'Desconocido',
            'Creado en': obs.creado_en.strftime('%d/%m/%Y %H:%M') if obs.creado_en else '',
            'Actualizado por': str(obs.actualizado_por) if obs.actualizado_por else '',
            'Actualizado en': obs.actualizado_en.strftime('%d/%m/%Y %H:%M') if obs.actualizado_en else '',
            'Fotos': 'Si' if obs.foto_1 or obs.foto_2 else 'No',
        }
        
        # Informacion del levantamiento si existe
        if hasattr(obs, 'levantamiento') and obs.levantamiento:
            lev = obs.levantamiento
            row.update({
                'Levantamiento - Estado': lev.get_estado_display(),
                'Levantamiento - Fecha': lev.fecha_levantamiento.strftime('%d/%m/%Y') if lev.fecha_levantamiento else '',
                'Levantamiento - Tiempo': lev.tiempo_levantamiento if lev.tiempo_levantamiento else '',
                'Levantamiento - Descripcion': lev.descripcion,
                'Levantamiento - Revisado por': str(lev.revisor) if lev.revisor else 'No revisado',
                'Levantamiento - Revisado en': lev.revisado_en.strftime('%d/%m/%Y %H:%M') if lev.revisado_en else '',
                'Levantamiento - Comentario revisor': lev.comentario_revisor if lev.comentario_revisor else '',
            })
        else:
            row.update({
                'Levantamiento - Estado': 'Sin levantamiento',
                'Levantamiento - Fecha': '',
                'Levantamiento - Tiempo': '',
                'Levantamiento - Descripcion': '',
                'Levantamiento - Revisado por': '',
                'Levantamiento - Revisado en': '',
                'Levantamiento - Comentario revisor': '',
            })
        
        data.append(row)
    
    # Crear el DataFrame
    df = pd.DataFrame(data)
    
    # Crear el archivo Excel en memoria
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Observaciones SSOMA', index=False)
        
        # Ajustar el ancho de las columnas
        worksheet = writer.sheets['Observaciones SSOMA']
        for i, col in enumerate(df.columns):
            max_length = max(
                df[col].astype(str).map(len).max(),
                len(col)
            ) + 2
            worksheet.column_dimensions[chr(65 + i)].width = min(max_length, 50)
    
    # Preparar la respuesta HTTP
    output.seek(0)
    filename = f'observaciones_ssoma_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename={filename}'
    
    return response
