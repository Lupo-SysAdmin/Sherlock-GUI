#!/bin/bash

# Colores para la terminal
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}[+] Iniciando instalación de Sherlock by Lupo...${NC}"

# 1. Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# 2. Instalar dependencias
echo -e "${BLUE}[+] Instalando librerías necesarias...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# 3. Crear el lanzador .desktop profesional
APP_PATH=$(pwd)
cat <<EOF > sherlock.desktop
[Desktop Entry]
Name=Sherlock Lupo
Exec=${APP_PATH}/venv/bin/python3 ${APP_PATH}/src/Sherlock.py
Icon=${APP_PATH}/assets/sherlock.png
Type=Application
Terminal=false
Categories=Network;Security;
EOF

# 4. Dar permisos al lanzador
chmod +x sherlock.desktop

echo -e "${GREEN}[✔] Instalación completada.${NC}"
echo -e "${GREEN}[✔] Puedes ejecutar el programa con: source venv/bin/activate && python3 src/Sherlock.py${NC}"
echo -e "${GREEN}[✔] O usar el acceso directo 'sherlock.desktop' creado en esta carpeta.${NC}"
