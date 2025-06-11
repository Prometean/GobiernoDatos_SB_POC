#!/usr/bin/env python3
"""
Superset Automation Script for Alpha Vantage Financial Data
===========================================================

Automatiza la creación de datasets, visualizaciones y dashboard en Apache Superset
para datos financieros obtenidos de Alpha Vantage API.

Autor: Analista de Gobierno de Datos
Organización: Superintendencia de Bancos
Fecha: Junio 2025
"""

import sqlite3
import pandas as pd
import requests
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import sys
import os

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('superset_automation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class SupersetConfig:
    """Configuración para conexión con Superset"""
    base_url: str = "http://localhost:8088"
    username: str = "admin"
    password: str = "admin"
    database_name: str = "Alpha Vantage DB"
    database_uri: str = "sqlite:////app/db/alpha_data.db"

@dataclass
class ChartConfig:
    """Configuración para creación de gráficos"""
    slice_name: str
    viz_type: str
    table_name: str
    params: Dict
    description: str = ""

class SupersetAutomator:
    """
    Clase principal para automatizar la creación de visualizaciones en Superset
    """
    
    def __init__(self, config: SupersetConfig):
        self.config = config
        self.session = requests.Session()
        self.csrf_token = None
        self.database_id = None
        self.datasets = {}


    def authenticate(self) -> bool:
        """Autenticación robusta vía login API con CSRF y JWT"""
        try:
            # Paso 1: Obtener token CSRF
            csrf_url = f"{self.config.base_url}/api/v1/security/csrf_token/"
            csrf_response = self.session.get(csrf_url)
            if csrf_response.status_code != 200:
                logger.error("❌ No se pudo obtener CSRF token")
                return False

            csrf_token = csrf_response.json().get("result")
            self.session.headers.update({
                "X-CSRFToken": csrf_token,
                "Content-Type": "application/json"
            })

            # Paso 2: Login con usuario y contraseña
            login_payload = {
                "username": self.config.username,
                "password": self.config.password,
                "provider": "db",
                "refresh": True
            }

            login_url = f"{self.config.base_url}/api/v1/security/login"
            login_response = self.session.post(login_url, json=login_payload)

            if login_response.status_code != 200:
                logger.error(f"❌ Falló login. Código: {login_response.status_code}")
                logger.error(f"Contenido: {login_response.text[:300]}")
                return False

            access_token = login_response.json().get("access_token")
            if not access_token:
                logger.error("❌ No se recibió token de acceso")
                return False

            self.session.headers.update({
                "Authorization": f"Bearer {access_token}"
            })

            logger.info("✅ Autenticación completada correctamente con token JWT")
            return True

        except Exception as e:
            logger.error(f"❌ Error durante autenticación: {str(e)}")
            return False


    def create_dataset(self, table_name: str) -> Optional[int]:
        """Crea un dataset en Superset para la tabla especificada"""
        try:
            # Verificar si el dataset ya existe
            datasets_response = self.session.get(f"{self.config.base_url}/api/v1/dataset/")
            
            if datasets_response.status_code == 200:
                datasets = datasets_response.json()["result"]
                for dataset in datasets:
                    if dataset["table_name"] == table_name and dataset["database"]["id"] == self.database_id:
                        dataset_id = dataset["id"]
                        self.datasets[table_name] = dataset_id
                        logger.info(f"✅ Dataset {table_name} ya existe con ID: {dataset_id}")
                        return dataset_id
            
            # Crear nuevo dataset
            dataset_data = {
                "database": self.database_id,
                "table_name": table_name,
                "owners": []
            }
            
            create_response = self.session.post(
                f"{self.config.base_url}/api/v1/dataset/",
                json=dataset_data
            )
            
            if create_response.status_code == 201:
                dataset_id = create_response.json()["id"]
                self.datasets[table_name] = dataset_id
                logger.info(f"✅ Dataset {table_name} creado con ID: {dataset_id}")
                return dataset_id
            else:
                logger.error(f"❌ Error creando dataset {table_name}: {create_response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error creando dataset {table_name}: {str(e)}")
            return None
    
    def create_chart(self, chart_config: ChartConfig) -> Optional[int]:
        """Crea un gráfico en Superset"""
        try:
            if chart_config.table_name not in self.datasets:
                logger.error(f"❌ Dataset {chart_config.table_name} no encontrado")
                return None
                
            chart_data = {
                "slice_name": chart_config.slice_name,
                "viz_type": chart_config.viz_type,
                "datasource_id": self.datasets[chart_config.table_name],
                "datasource_type": "table",
                "params": json.dumps(chart_config.params),
                "description": chart_config.description
            }
            
            create_response = self.session.post(
                f"{self.config.base_url}/api/v1/chart/",
                json=chart_data
            )
            
            if create_response.status_code == 201:
                chart_id = create_response.json()["id"]
                logger.info(f"✅ Gráfico '{chart_config.slice_name}' creado con ID: {chart_id}")
                return chart_id
            else:
                logger.error(f"❌ Error creando gráfico '{chart_config.slice_name}': {create_response.status_code}")
                logger.error(f"Response: {create_response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error creando gráfico '{chart_config.slice_name}': {str(e)}")
            return None
    
    def create_dashboard(self, dashboard_name: str, chart_ids: List[int]) -> Optional[int]:
        """Crea un dashboard con los gráficos especificados"""
        try:
            # Configuración del layout del dashboard (2 gráficos por fila)
            layout = {
                "GRID_ID": {
                    "children": [],
                    "id": "GRID_ID",
                    "type": "GRID"
                }
            }
            
            # Agregar gráficos al layout
            row_height = 50
            chart_width = 50
            current_row = 0
            
            for i, chart_id in enumerate(chart_ids):
                col_position = (i % 2) * chart_width
                if i > 0 and i % 2 == 0:
                    current_row += row_height
                    
                chart_component = {
                    "children": [],
                    "id": f"CHART-{chart_id}",
                    "meta": {
                        "chartId": chart_id,
                        "height": row_height,
                        "width": chart_width
                    },
                    "type": "CHART"
                }
                
                layout["GRID_ID"]["children"].append(chart_component)
            
            dashboard_data = {
                "dashboard_title": dashboard_name,
                "slug": dashboard_name.lower().replace(" ", "-"),
                "position_json": json.dumps(layout),
                "published": True
            }
            
            create_response = self.session.post(
                f"{self.config.base_url}/api/v1/dashboard/",
                json=dashboard_data
            )
            
            if create_response.status_code == 201:
                dashboard_id = create_response.json()["id"]
                logger.info(f"✅ Dashboard '{dashboard_name}' creado con ID: {dashboard_id}")
                return dashboard_id
            else:
                logger.error(f"❌ Error creando dashboard '{dashboard_name}': {create_response.status_code}")
                logger.error(f"Response: {create_response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error creando dashboard '{dashboard_name}': {str(e)}")
            return None

def load_csv_to_sqlite(csv_files: List[str], db_path: str) -> bool:
    """Carga archivos CSV a SQLite si no existen"""
    try:
        conn = sqlite3.connect(db_path)
        
        for csv_file in csv_files:
            if not Path(csv_file).exists():
                logger.warning(f"⚠️ Archivo {csv_file} no encontrado")
                continue
                
            table_name = Path(csv_file).stem
            
            # Verificar si la tabla ya existe
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            
            if cursor.fetchone():
                logger.info(f"✅ Tabla {table_name} ya existe en la base de datos")
                continue
            
            # Cargar CSV a SQLite
            df = pd.read_csv(csv_file)
            df.to_sql(table_name, conn, if_exists='replace', index=False)
            logger.info(f"✅ Tabla {table_name} creada en la base de datos con {len(df)} registros")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error cargando datos a SQLite: {str(e)}")
        return False

def get_chart_configurations() -> List[ChartConfig]:
    """Define las configuraciones de los gráficos a crear"""
    return [
        ChartConfig(
            slice_name="Revenue Timeline",
            viz_type="line",
            table_name="income_statement",
            params={
                "metrics": ["totalRevenue"],
                "groupby": ["date"],
                "time_grain_sqla": "P1M",
                "show_legend": True,
                "line_interpolation": "linear"
            },
            description="Evolución temporal de los ingresos totales"
        ),
        ChartConfig(
            slice_name="Operating Cash Flow",
            viz_type="dist_bar",
            table_name="cash_flow",
            params={
                "metrics": ["operatingCashflow"],
                "groupby": ["date"],
                "show_legend": False,
                "show_bar_value": True
            },
            description="Flujo de caja operativo por período"
        ),
        ChartConfig(
            slice_name="Assets vs Liabilities",
            viz_type="line",
            table_name="balance_sheet",
            params={
                "metrics": ["totalAssets", "totalLiabilities"],
                "groupby": ["date"],
                "time_grain_sqla": "P1M",
                "show_legend": True,
                "line_interpolation": "linear"
            },
            description="Comparación entre activos totales y pasivos totales"
        ),
        ChartConfig(
            slice_name="Bank Overview",
            viz_type="table",
            table_name="overview",
            params={
                "all_columns": ["symbol", "name", "sector", "industry", "marketCapitalization", "peRatio"],
                "page_length": 10
            },
            description="Información general y métricas clave del banco"
        )
    ]

def main():
    """Función principal del script"""
    logger.info("🚀 Iniciando automatización de Superset...")
    
    # Configuración
    config = SupersetConfig()

    csv_files = [
        "/app/data/balance_sheet.csv",
        "/app/data/cash_flow.csv", 
        "/app/data/income_statement.csv",
        "/app/data/overview.csv"
    ]

    db_path = "/app/db/alpha_data.db"
    
    # 1. Cargar datos CSV a SQLite
    logger.info("📊 Cargando datos CSV a SQLite...")
    if not load_csv_to_sqlite(csv_files, db_path):
        logger.error("❌ Error cargando datos. Abortando proceso.")
        return False
    
    # 2. Inicializar automatizador de Superset
    automator = SupersetAutomator(config)
    
    # 3. Autenticar
    logger.info("🔐 Autenticando en Superset...")
    if not automator.authenticate():
        logger.error("❌ Error de autenticación. Generando guía manual...")
        generate_manual_commands()
        return False
    
    # 4. Configurar base de datos
    logger.info("🗄️ Configurando conexión a base de datos...")
    if not automator.ensure_database_exists():
        logger.error("❌ Error configurando base de datos. Generando guía manual...")
        generate_manual_commands()
        return False
    
    # 5. Crear datasets
    logger.info("📋 Creando datasets...")
    table_names = ["balance_sheet", "cash_flow", "income_statement", "overview"]
    for table_name in table_names:
        automator.create_dataset(table_name)
    
    # 6. Crear gráficos
    logger.info("📈 Creando visualizaciones...")
    chart_configs = get_chart_configurations()
    chart_ids = []
    
    for config in chart_configs:
        chart_id = automator.create_chart(config)
        if chart_id:
            chart_ids.append(chart_id)
    
    # 7. Crear dashboard
    if chart_ids:
        logger.info("🎛️ Creando dashboard...")
        dashboard_id = automator.create_dashboard("Análisis Financiero Alpha Vantage", chart_ids)
        
        if dashboard_id:
            logger.info(f"✅ ¡Dashboard creado exitosamente! ID: {dashboard_id}")
            logger.info(f"🔗 Accede en: {config.base_url}/superset/dashboard/{dashboard_id}/")
        else:
            logger.error("❌ Error creando dashboard")
    else:
        logger.error("❌ No se pudieron crear gráficos. Generando guía manual...")
        generate_manual_commands()
    
    logger.info("🎉 Proceso de automatización completado")
    return True

def generate_manual_commands():
    """Genera comandos manuales para crear las visualizaciones"""
    logger.info("📋 Generando guía de comandos manuales...")
    
    manual_guide = """
    
    🚀 GUÍA MANUAL - CREACIÓN DE VISUALIZACIONES
    ============================================
    
    Como la automatización falló, aquí tienes los pasos manuales:
    
    1. 🌐 Accede a Superset: http://localhost:8088
    2. 🔐 Login: admin / admin
    
    3. 🗄️ CREAR BASE DE DATOS:
       - Ir a: Data → Databases → + Database
       - Database Name: Alpha Vantage DB
       - SQLAlchemy URI: sqlite:////app/db/alpha_data.db
       - Test Connection → Connect
    
    4. 📊 CREAR DATASETS (para cada tabla):
       - Ir a: Data → Datasets → + Dataset
       - Database: Alpha Vantage DB
       - Schema: main
       - Tables: balance_sheet, cash_flow, income_statement, overview
    
    5. 📈 CREAR VISUALIZACIONES:
    
       📊 REVENUE TIMELINE:
       - Dataset: income_statement
       - Chart Type: Line Chart
       - Metrics: totalRevenue
       - Dimensions: date
       - SQL: SELECT date, totalRevenue FROM income_statement ORDER BY date
    
       📊 OPERATING CASH FLOW:
       - Dataset: cash_flow  
       - Chart Type: Bar Chart
       - Metrics: operatingCashflow
       - Dimensions: date
       - SQL: SELECT date, operatingCashflow FROM cash_flow ORDER BY date
    
       📊 ASSETS VS LIABILITIES:
       - Dataset: balance_sheet
       - Chart Type: Line Chart
       - Metrics: totalAssets, totalLiabilities
       - Dimensions: date
       - SQL: SELECT date, totalAssets, totalLiabilities FROM balance_sheet ORDER BY date
    
       📊 BANK OVERVIEW:
       - Dataset: overview
       - Chart Type: Table
       - Columns: symbol, name, sector, industry, marketCapitalization, peRatio
       - SQL: SELECT symbol, name, sector, industry, marketCapitalization, peRatio FROM overview
    
    6. 🎛️ CREAR DASHBOARD:
       - Ir a: Dashboards → + Dashboard
       - Title: "Análisis Financiero Alpha Vantage"
       - Agregar los 4 gráficos creados
       - Organizar en grilla 2x2
    
    7. ✅ VERIFICAR DATOS:
       - SQL Lab → Alpha Vantage DB
       - Ejecutar: SELECT COUNT(*) FROM balance_sheet;
       - Ejecutar: SELECT COUNT(*) FROM cash_flow;
       - Ejecutar: SELECT COUNT(*) FROM income_statement;
       - Ejecutar: SELECT COUNT(*) FROM overview;
    
    🎯 RESULTADO ESPERADO:
    Dashboard con 4 visualizaciones financieras profesionales
    listo para presentación en la prueba técnica.
    
    """
    
    print(manual_guide)
    logger.info("📝 Guía manual generada. Consulta la salida de consola para los pasos detallados.")
    
    # Crear archivo con la guía
    try:
        with open("/app/superset_home/manual_guide.txt", "w") as f:
            f.write(manual_guide)
        logger.info("📄 Guía guardada en: /app/superset_home/manual_guide.txt")
    except Exception as e:
        logger.error(f"❌ Error guardando guía: {str(e)}")

def verify_data():
    """Verifica que los datos estén correctamente cargados"""
    try:
        conn = sqlite3.connect("/app/db/alpha_data.db")
        cursor = conn.cursor()
        
        tables = ["balance_sheet", "cash_flow", "income_statement", "overview"]
        
        logger.info("🔍 Verificando datos en la base de datos...")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            logger.info(f"✅ Tabla {table}: {count} registros")
            
            # Mostrar primeras columnas
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [row[1] for row in cursor.fetchall()]
            logger.info(f"   Columnas: {', '.join(columns[:5])}{'...' if len(columns) > 5 else ''}")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error verificando datos: {str(e)}")
        return False

if __name__ == "__main__":
    # Verificar datos primero
    verify_data()
    
    # Intentar automatización
    success = main()
    
    if not success:
        logger.info("🔧 La automatización falló, pero los datos están listos.")
        logger.info("📋 Consulta la guía manual generada para continuar.")
        logger.info("🌐 Accede a Superset: http://localhost:8088 (admin/admin)")
    
    sys.exit(0 if success else 1)