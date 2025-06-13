import os
import csv
from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings

class Command(BaseCommand):
    help = 'Exporta todas las tablas de la base de datos a archivos CSV con codificación UTF-8-SIG'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output-dir',
            dest='output_dir',
            default='',
            help='Directorio donde se guardarán los archivos CSV',
        )
    
    def handle(self, *args, **options):
        output_dir = options['output_dir']
        export_dir = self.export_all_tables_to_csv(output_dir)
        self.stdout.write(self.style.SUCCESS(f"Exportación completada. Los archivos CSV se encuentran en: {export_dir}"))
    
    def export_all_tables_to_csv(self, output_dir=''):
        """Exporta todas las tablas de la base de datos a archivos CSV."""
        # Crear directorio para los archivos CSV si no existe
        if output_dir:
            export_dir = output_dir
        else:
            # Por defecto, usar un directorio db_export en la raíz del proyecto
            export_dir = os.path.join(settings.BASE_DIR.parent, 'app', 'db_export')
            
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)
    
        # Obtener todas las tablas de la base de datos
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            tables = [row[0] for row in cursor.fetchall()]
        
        # Excluir tablas de Django que no necesitamos exportar
        excluded_tables = [
            'django_migrations', 'django_session', 'django_admin_log', 
            'auth_permission', 'django_content_type'
        ]
        
        tables = [table for table in tables if table not in excluded_tables]
        
        self.stdout.write(f"Se encontraron {len(tables)} tablas para exportar.")
        
        # Exportar cada tabla a un archivo CSV
        for table_name in tables:
            try:
                csv_file_path = os.path.join(export_dir, f"{table_name}.csv")
                with connection.cursor() as cursor:
                    # Obtener nombres de columnas
                    cursor.execute(f"SELECT * FROM {table_name} LIMIT 0")
                    column_names = [desc[0] for desc in cursor.description]
                    
                    # Obtener datos
                    cursor.execute(f"SELECT * FROM {table_name}")
                    rows = cursor.fetchall()
                    
                    # Escribir a CSV con codificación UTF-8-SIG
                    with open(csv_file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow(column_names)
                        writer.writerows(rows)
                
                self.stdout.write(f"Tabla {table_name} exportada a {csv_file_path} ({len(rows)} filas)")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error al exportar la tabla {table_name}: {e}"))
        
        return export_dir
