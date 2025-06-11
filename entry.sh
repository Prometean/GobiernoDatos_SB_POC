#!/bin/bash

set -e

echo "🚀 Iniciando Superset con automatización mejorada..."

# Instalar dependencias adicionales
echo "📦 Installing additional dependencies..."
pip install --no-cache-dir -r /app/requirements.txt

# Crear directorios necesarios
mkdir -p /app/superset_home/uploads
chmod 777 /app/superset_home/uploads

# Configurar permisos
chown -R superset:superset /app/superset_home

# Inicializar base de datos
echo "🗄️ Initializing database..."
superset db upgrade

# Crear usuario admin si no existe
echo "👤 Creating admin user..."
superset fab create-admin \
    --username admin \
    --firstname Admin \
    --lastname User \
    --email admin@example.com \
    --password admin || true

# Inicializar Superset
echo "🔧 Initializing Superset..."
superset init

# Copiar script de automatización si existe
if [ -f "/app/superset_automation.py" ]; then
    echo "📋 Copying automation script..."
    cp /app/superset_automation.py /app/superset_home/
    chmod +x /app/superset_home/superset_automation.py
fi

# Iniciar servidor en background
echo "🌐 Starting Superset server..."
superset run -h 0.0.0.0 -p 8088 --with-threads --reload --debugger &

# Esperar más tiempo y verificar múltiples endpoints
echo "⏳ Waiting for Superset to be ready..."
MAX_ATTEMPTS=30
ATTEMPT=1

while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
    if curl --output /dev/null --silent --head --fail http://localhost:8088/login/ 2>/dev/null; then
        echo "✅ Superset login page is ready!"
        break
    fi
    
    if curl --output /dev/null --silent --head --fail http://localhost:8088/api/v1/security/csrf_token/ 2>/dev/null; then
        echo "✅ Superset API is ready!"
        break
    fi
    
    printf "."
    sleep 2
    ATTEMPT=$((ATTEMPT + 1))
done

if [ $ATTEMPT -gt $MAX_ATTEMPTS ]; then
    echo "❌ Superset no responde después de $MAX_ATTEMPTS intentos"
    echo "📋 Verificando logs de Superset..."
    ps aux | grep superset || true
    exit 1
fi

echo "✅ Superset is ready!"

# Esperar un poco más para asegurar que todo esté listo
echo "⏳ Waiting additional 10 seconds for full initialization..."
sleep 10

# Ejecutar script de automatización si existe
if [ -f "/app/superset_home/superset_automation.py" ]; then
    echo "🤖 Running automation script..."
    cd /app/superset_home
    
    # Ejecutar con manejo de errores
    if python superset_automation.py; then
        echo "✅ Automation completed successfully!"
    else
        echo "⚠️ Automation failed, but Superset is running"
        echo "📋 Check logs for details or run manually"
        echo "🌐 Access Superset at: http://localhost:8088 (admin/admin)"
    fi
else
    echo "⚠️ Automation script not found. Run manually if needed."
fi

# Mantener el contenedor corriendo
echo "🎉 Setup complete! Superset is running on http://localhost:8088"

# Mostrar información útil
echo "========================================"
echo "🔗 Superset URL: http://localhost:8088"
echo "👤 Username: admin"
echo "🔑 Password: admin"
echo "📊 Dashboard will be available at:"
echo "   http://localhost:8088/superset/dashboard/"
echo "========================================"

# Mantener el proceso principal corriendo
wait