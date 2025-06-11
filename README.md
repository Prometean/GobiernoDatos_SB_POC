# GobiernoDatos_SB_POC
Prueba de concepto (POC) para plataforma analítica (Superintendencia de Bancos)

## Superset Config

Se incluye un archivo `superset_config.py` con flags básicos para habilitar la carga de archivos CSV/XLSX desde la interfaz y permitir conexiones a bases SQLite dentro del contenedor.

Montar el archivo en la imagen de Superset añadiendo en `docker-compose.yml`:

```yaml
  volumes:
    - ./staging:/app/superset_home
    - ./superset_config.py:/app/pythonpath/superset_config.py
```

Con esto Superset podrá reconocer el directorio `staging/` como su `superset_home` y aceptará la carga manual de archivos.
