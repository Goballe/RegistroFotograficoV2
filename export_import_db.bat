@echo off
REM Script para exportar e importar la base de datos a archivos CSV

echo === Herramienta de Exportacion/Importacion de Base de Datos ===
echo.

if "%1"=="export" (
    echo Exportando todas las tablas a archivos CSV...
    docker exec -it django_web python manage.py export_db_to_csv
    echo Los archivos CSV se han guardado en la carpeta db_export
    goto :EOF
)

if "%1"=="import" (
    echo ADVERTENCIA: Esto sobrescribira todos los datos actuales en la base de datos.
    set /p confirm=Esta seguro que desea continuar? (s/n): 
    if /i "%confirm%"=="s" (
        echo Importando datos desde archivos CSV...
        docker exec -it django_web python manage.py import_csv_to_db
        echo Importacion completada.
    ) else (
        echo Operacion cancelada.
    )
    goto :EOF
)

echo Uso:
echo   export_import_db.bat export   # Exportar todas las tablas a archivos CSV
echo   export_import_db.bat import   # Importar datos desde archivos CSV
