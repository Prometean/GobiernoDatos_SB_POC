#!/bin/bash

set -e

# Instalar dependencias adicionales
echo "Installing additional dependencies..."
pip install --no-cache-dir -r /app/requirements.txt

# Crear directorios necesarios
mkdir -p /app/superset_home/uploads
chmod 777 /app/superset_home/uploads

# Configurar permisos
chown -R superset:superset /app/superset_home

# Inicializar base de datos
echo "Initializing database..."
superset db upgrade

# Crear usuario admin si no existe
echo "Creating admin user..."
superset fab create-admin \
    --username admin \
    --firstname Admin \
    --lastname User \
    --email admin@example.com \
    --password admin || true

# Saltar carga de ejemplos para acelerar inicio
echo "Skipping examples to speed up startup..."

# Inicializar Superset
echo "Initializing Superset..."
superset init

# Iniciar servidor
echo "Starting Superset server..."
superset run -h 0.0.0.0 -p 8088 --with-threads --reload --debugger