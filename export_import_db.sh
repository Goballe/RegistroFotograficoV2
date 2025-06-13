#!/bin/bash
# Script para exportar e importar la base de datos a archivos CSV

# Colores para mensajes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Herramienta de Exportación/Importación de Base de Datos ===${NC}"
echo

if [ "$1" == "export" ]; then
    echo -e "${GREEN}Exportando todas las tablas a archivos CSV...${NC}"
    docker exec -it django_web python manage.py export_db_to_csv
    echo -e "${GREEN}Los archivos CSV se han guardado en la carpeta db_export${NC}"

elif [ "$1" == "import" ]; then
    echo -e "${YELLOW}ADVERTENCIA: Esto sobrescribirá todos los datos actuales en la base de datos.${NC}"
    read -p "¿Está seguro que desea continuar? (s/n): " confirm
    if [ "$confirm" == "s" ] || [ "$confirm" == "S" ]; then
        echo -e "${GREEN}Importando datos desde archivos CSV...${NC}"
        docker exec -it django_web python manage.py import_csv_to_db
        echo -e "${GREEN}Importación completada.${NC}"
    else
        echo -e "${RED}Operación cancelada.${NC}"
    fi

else
    echo -e "${YELLOW}Uso:${NC}"
    echo "  ./export_import_db.sh export   # Exportar todas las tablas a archivos CSV"
    echo "  ./export_import_db.sh import   # Importar datos desde archivos CSV"
fi
