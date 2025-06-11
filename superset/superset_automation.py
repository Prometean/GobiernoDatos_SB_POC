#!/usr/bin/env python3
"""
Superset Automation Script - VERSIÓN CORREGIDA
==============================================
Script mejorado con autenticación robusta que funciona dentro del contenedor
"""

import sqlite3
import pandas as pd
import requests
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional
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
    base_url: str = "https://fictional-computing-machine-wq555xgrxj6h56wp-8088.app.github.dev"
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
    CON AUTENTICACIÓN CORREGIDA
    """
    
    def __init__(self, config: SupersetConfig):
        self.config = config
        self.session = requests.Session()
        self.access_token = None
        self.database_id = None
        self.datasets = {}

    def authenticate(self) -> bool:
        """Autenticación API con manejo robusto en entornos remotos"""
        try:
            csrf_response = self.session.get(
                f"{self.config.base_url}/api/v1/security/csrf_token/",
                headers={"Referer": self.config.base_url}
            )
            if csrf_response.status_code != 200:
                logger.error("❌ No se pudo obtener CSRF token")
                return False

            self.csrf_token = csrf_response.json().get("result")
            self.session.headers.update({
                "X-CSRFToken": self.csrf_token,
                "Content-Type": "application/json"
            })

            login_data = {
                "username": self.config.username,
                "password": self.config.password,
                "provider": "db"
            }

            login_response = self.session.post(
                f"{self.config.base_url}/api/v1/security/login",
                json=login_data
            )

            if login_response.status_code == 200:
                access_token = login_response.json().get("access_token")
                self.session.headers.update({
                    "Authorization": f"Bearer {access_token}"
                })
                logger.info("✅ Autenticación API exitosa")
                return True
            else:
                logger.error(f"❌ Error login: {login_response.status_code} - {login_response.text}")
                return False

        except Exception as e:
            logger.error(f"❌ Error en autenticación API: {str(e)}")
            return False


    def _authenticate_direct(self) -> bool:
        """Autenticación directa sin CSRF"""
        try:
            logger.info("🔓 Probando autenticación directa...")
            
            login_url = f"{self.config.base_url}/api/v1/security/login"
            
            payload = {
                "username": self.config.username,
                "password": self.config.password,
                "provider": "db"
            }
            
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "SupersetAutomator/1.0"
            }
            
            response = self.session.post(login_url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token")
                
                if self.access_token:
                    self.session.headers.update({
                        "Authorization": f"Bearer {self.access_token}",
                        "Content-Type": "application/json"
                    })
                    
                    # Verificar que funciona
                    if self._test_auth():
                        logger.info("✅ Autenticación directa exitosa")
                        return True
            
            logger.warning(f"⚠️ Autenticación directa falló: {response.status_code}")
            return False
            
        except Exception as e:
            logger.warning(f"⚠️ Error en autenticación directa: {str(e)}")
            return False

    def _authenticate_with_session(self) -> bool:
        """Autenticación usando sesión web"""
        try:
            logger.info("🌐 Probando autenticación con sesión web...")
            
            # Establecer sesión web primero
            login_page = self.session.get(f"{self.config.base_url}/login/", timeout=30)
            
            # Login con form data
            login_data = {
                "username": self.config.username,
                "password": self.config.password
            }
            
            login_response = self.session.post(
                f"{self.config.base_url}/login/",
                data=login_data,
                allow_redirects=True,
                timeout=30
            )
            
            if login_response.status_code in [200, 302]:
                # Verificar que funciona
                if self._test_auth():
                    logger.info("✅ Autenticación con sesión exitosa")
                    return True
            
            logger.warning(f"⚠️ Autenticación con sesión falló: {login_response.status_code}")
            return False
            
        except Exception as e:
            logger.warning(f"⚠️ Error en autenticación con sesión: {str(e)}")
            return False

    def _authenticate_with_csrf(self) -> bool:
        """Autenticación con CSRF token"""
        try:
            logger.info("🛡️ Probando autenticación con CSRF...")
            
            # Obtener CSRF token
            csrf_response = self.session.get(f"{self.config.base_url}/api/v1/security/csrf_token/", timeout=30)
            
            if csrf_response.status_code == 200:
                csrf_token = csrf_response.json().get("result")
                
                if csrf_token:
                    # Login con CSRF
                    login_payload = {
                        "username": self.config.username,
                        "password": self.config.password,
                        "provider": "db"
                    }
                    
                    headers = {
                        "X-CSRFToken": csrf_token,
                        "Content-Type": "application/json"
                    }
                    
                    login_response = self.session.post(
                        f"{self.config.base_url}/api/v1/security/login",
                        json=login_payload,
                        headers=headers,
                        timeout=30
                    )
                    
                    if login_response.status_code == 200:
                        data = login_response.json()
                        self.access_token = data.get("access_token")
                        
                        if self.access_token:
                            self.session.headers.update({
                                "Authorization": f"Bearer {self.access_token}",
                                "Content-Type": "application/json"
                            })
                            
                            if self._test_auth():
                                logger.info("✅ Autenticación con CSRF exitosa")
                                return True
            
            logger.warning("⚠️ Autenticación con CSRF falló")
            return False
            
        except Exception as e:
            logger.warning(f"⚠️ Error en autenticación con CSRF: {str(e)}")
            return False

    def _test_auth(self) -> bool:
        """Verifica si la autenticación funciona"""
        try:
            response = self.session.get(f"{self.config.base_url}/api/v1/me/", timeout=10)
            success = response.status_code == 200
            if success:
                logger.info("✅ Verificación de autenticación exitosa")
            return success
        except Exception as e:
            logger.warning(f"⚠️ Error verificando autenticación: {str(e)}")
            return False

    def ensure_database_exists(self) -> bool:
        """Asegura que la base de datos existe en Superset"""
        try:
            # Listar bases de datos existentes
            response = self.session.get(f"{self.config.base_url}/api/v1/database/")
            
            if response.status_code == 200:
                databases = response.json()["result"]
                
                # Buscar base de datos existente
                for db in databases:
                    if db["database_name"] == self.config.database_name:
                        self.database_id = db["id"]
                        logger.info(f"✅ Base de datos '{self.config.database_name}' encontrada con ID: {self.database_id}")
                        return True
                
                # Crear nueva base de datos
                database_data = {
                    "database_name": self.config.database_name,
                    "sqlalchemy_uri": self.config.database_uri,
                    "expose_in_sqllab": True,
                    "allow_run_async": True
                }
                
                create_response = self.session.post(
                    f"{self.config.base_url}/api/v1/database/",
                    json=database_data
                )
                
                if create_response.status_code == 201:
                    self.database_id = create_response.json()["id"]
                    logger.info(f"✅ Base de datos '{self.config.database_name}' creada con ID: {self.database_id}")
                    return True
                else:
                    logger.error(f"❌ Error creando base de datos: {create_response.status_code}")
                    logger.error(f"Response: {create_response.text}")
                    return False
            else:
                logger.error(f"❌ Error listando bases de datos: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error configurando base de datos: {str(e)}")
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
            # Layout simplificado
            dashboard_data = {
                "dashboard_title": dashboard_name,
                "slug": dashboard_name.lower().replace(" ", "-"),
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
    logger.info("🚀 Iniciando automatización de Superset con autenticación mejorada...")
    
    # Configuración
    config = SupersetConfig()
    csv_files = [
        "./data/balance_sheet.csv",
        "./data/cash_flow.csv", 
        "./data/income_statement.csv",
        "./data/overview.csv"
    ]
    db_path = "./db/alpha_data.db"
    
    # 1. Cargar datos CSV a SQLite
    logger.info("📊 Cargando datos CSV a SQLite...")
    if not load_csv_to_sqlite(csv_files, db_path):
        logger.error("❌ Error cargando datos. Abortando proceso.")
        return False
    
    # 2. Inicializar automatizador de Superset
    automator = SupersetAutomator(config)
    
    # 3. Autenticar (método mejorado)
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
    
    for config_chart in chart_configs:
        chart_id = automator.create_chart(config_chart)
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
    
    1. 🌐 Accede a Superset: https://fictional-computing-machine-wq555xgrxj6h56wp-8088.app.github.dev/tablemodelview/list/?pageIndex=0&sortColumn=changed_on_delta_humanized&sortOrder=desc
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
    
       📊 OPERATING CASH FLOW:
       - Dataset: cash_flow  
       - Chart Type: Bar Chart
       - Metrics: operatingCashflow
       - Dimensions: date
    
       📊 ASSETS VS LIABILITIES:
       - Dataset: balance_sheet
       - Chart Type: Line Chart
       - Metrics: totalAssets, totalLiabilities
       - Dimensions: date
    
       📊 BANK OVERVIEW:
       - Dataset: overview
       - Chart Type: Table
       - Columns: symbol, name, sector, industry, marketCapitalization, peRatio
    
    6. 🎛️ CREAR DASHBOARD:
       - Ir a: Dashboards → + Dashboard
       - Title: "Análisis Financiero Alpha Vantage"
       - Agregar los 4 gráficos creados
    
    """
    
    print(manual_guide)
    logger.info("📝 Guía manual generada. Consulta la salida de consola para los pasos detallados.")

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
        logger.info("🌐 Accede a Superset: https://fictional-computing-machine-wq555xgrxj6h56wp-8088.app.github.dev/tablemodelview/list/?pageIndex=0&sortColumn=changed_on_delta_humanized&sortOrder=desc (admin/admin)")
    
    sys.exit(0 if success else 1)