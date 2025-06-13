import pandas
import os
import psycopg2


actual_path = os.path.abspath(__file__)
print(actual_path)

# conn = psycopg2.connect(
#     host="postgres_db",
#     port="5432",
import pandas as pd
from sqlalchemy import create_engine

def generate_random_df():
    """
    Genera un DataFrame aleatorio con datos de observaciones.
    """
    import random
    from datetime import datetime, timedelta
    
    # Datos de ejemplo para cada campo
    items = list(range(1, 11))  # 1 al 10
    semanas = [f'Semana {i}' for i in range(1, 9)]
    puntos_inspeccion = ['Estructura Principal', 'Cimentación', 'Instalaciones Eléctricas', 
                        'Fontanería', 'Acabados', 'Cubierta', 'Fachada', 'Áreas Comunes']
    subclasificaciones = ['Seguridad', 'Calidad', 'Medio Ambiente', 'Salud Ocupacional']
    descripciones = [
        'Falta de protección en andamios',
        'Conexiones eléctricas expuestas',
        'Materiales mal almacenados',
        'Falta de señalización',
        'Orden y limpieza inadecuados',
        'Falta de EPP',
        'Protecciones colectivas faltantes',
        'Condiciones inseguras en altura'
    ]
    niveles_riesgo = ['Alto', 'Medio', 'Bajo']
    recomendaciones = [
        'Implementar barandas de protección',
        'Asegurar conexiones eléctricas',
        'Reubicar materiales según normativa',
        'Colocar señalización adecuada',
        'Mantener el área limpia y ordenada',
        'Proveer EPP adecuado',
        'Instalar protecciones colectivas',
        'Corregir condiciones inseguras'
    ]
    estados = ['Pendiente', 'En Proceso', 'Atendido', 'Cerrado']
    
    # Generar fechas aleatorias de los últimos 30 días
    def random_date():
        return (datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%d/%m/%Y')
    
    # Generar datos de ejemplo
    data = []
    for i in range(1, 21):  # 20 registros de ejemplo
        data.append({
            'Ítem': f'OB-{1000 + i}',
            'Sem de obs': random.choice(semanas),
            'Fecha': random_date(),
            'Punto de inspección': random.choice(puntos_inspeccion),
            'Sub Clasificación': random.choice(subclasificaciones),
            'Descripción de la observación': random.choice(descripciones),
            'Nivel de riesgo': random.choice(niveles_riesgo),
            'Fotografía 01': f'foto_{i}_01.jpg',
            'Fotografía 02': f'foto_{i}_02.jpg',
            'Recomendación para Levantamiento': random.choice(recomendaciones),
            'Estado': random.choice(estados)
        })
    
    # Crear DataFrame
    random_df = pd.DataFrame(data)
    return random_df

def get_database_connection():
    """
    Crea y devuelve una conexión a la base de datos PostgreSQL.
    """
    try:
        engine = create_engine('postgresql://postgres:postgres@postgres_db:5432/registro_fotografico')
        return engine
    except Exception as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None

def save_to_database(df, table_name='tabla_random'):
    """
    Guarda un DataFrame en la base de datos.
    """
    try:
        engine = get_database_connection()
        if engine is not None:
            df.to_sql(table_name, engine, if_exists='replace', index=False)
            return True
        return False
    except Exception as e:
        print(f"Error al guardar en la base de datos: {e}")
        return False
