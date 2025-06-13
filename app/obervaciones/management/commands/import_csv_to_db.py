import os
import csv
import glob
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.conf import settings

class Command(BaseCommand):
    help = 'Importa datos de archivos CSV a la base de datos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--input-dir',
            dest='input_dir',
            default='',
            help='Directorio donde se encuentran los archivos CSV a importar',
        )

    def handle(self, *args, **options):
        input_dir = options['input_dir']
        
        # Si no se especifica un directorio, usar el directorio por defecto
        if not input_dir:
            input_dir = os.path.join(settings.BASE_DIR.parent, 'app', 'db_export')
        
        success = self.import_csv_to_db(input_dir)
        if success:
            self.stdout.write(self.style.SUCCESS("Importación completada exitosamente."))
        else:
            self.stdout.write(self.style.ERROR("La importación falló."))

    def import_csv_to_db(self, csv_dir):
        """Importa datos de archivos CSV a la base de datos."""
        if not os.path.exists(csv_dir):
            self.stdout.write(self.style.ERROR(f"El directorio {csv_dir} no existe."))
            return False
        
        # Obtener todos los archivos CSV en el directorio
        csv_files = glob.glob(os.path.join(csv_dir, "*.csv"))
        if not csv_files:
            self.stdout.write(self.style.ERROR(f"No se encontraron archivos CSV en {csv_dir}."))
            return False
        
        self.stdout.write(f"Se encontraron {len(csv_files)} archivos CSV para importar.")
    
        # Deshabilitar restricciones de clave foránea temporalmente
        with connection.cursor() as cursor:
            cursor.execute("SET CONSTRAINTS ALL DEFERRED;")
        
        # Importar cada archivo CSV a su tabla correspondiente
        for csv_file_path in sorted(csv_files):
            table_name = os.path.basename(csv_file_path).replace('.csv', '')
            try:
                # Leer datos del CSV
                with open(csv_file_path, 'r', encoding='utf-8-sig') as csvfile:
                    reader = csv.reader(csvfile)
                    column_names = next(reader)  # Primera fila son los nombres de columnas
                    rows = list(reader)
                
                if not rows:
                    self.stdout.write(f"Archivo {csv_file_path} está vacío. Saltando.")
                    continue
                
                # Limpiar la tabla antes de importar
                with connection.cursor() as cursor:
                    cursor.execute(f"TRUNCATE TABLE {table_name} CASCADE;")
                    
                    # Preparar la consulta SQL para inserción
                    placeholders = ', '.join(['%s'] * len(column_names))
                    columns = ', '.join([f'"{col}"' for col in column_names])
                    sql = f'INSERT INTO {table_name} ({columns}) VALUES ({placeholders})'
                    
                    # Insertar datos
                    cursor.executemany(sql, rows)
                
                self.stdout.write(f"Tabla {table_name} importada desde {csv_file_path} ({len(rows)} filas)")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error al importar la tabla {table_name}: {e}"))
    
        # Restablecer secuencias (autoincrement)
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT table_name, column_name, column_default
                FROM information_schema.columns
                WHERE column_default LIKE 'nextval%'
            """)
            sequences = cursor.fetchall()
            
            for table, column, default in sequences:
                seq_name = default.split("'")[1]
                cursor.execute(f"""
                    SELECT setval('{seq_name}', 
                        COALESCE((SELECT MAX({column}) FROM {table}), 1), 
                        COALESCE((SELECT MAX({column}) FROM {table}) > 0, false)
                    )
                """)
                self.stdout.write(f"Secuencia {seq_name} para {table}.{column} actualizada")
        
        return True
