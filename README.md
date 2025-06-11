# GobiernoDatos_SB_POC

Plataforma de Analítica Financiera para la Superintendencia de Bancos (SB)

**Candidato:** Ean Jiménez  
**Fecha:** Junio 2025

---

## Descripción del Proyecto

Este repositorio implementa una prueba técnica para la Superintendencia de Bancos de la República Dominicana. El objetivo es construir una **plataforma analítica avanzada**, alineada con los cuatro ejercicios definidos en el documento oficial `20240926_Prueba_Gobierno_Datos_Encargado.pdf`, utilizando datos reales obtenidos desde la API de [Alpha Vantage](https://www.alphavantage.co/).

La solución integra procesos de:
- Ingesta de datos financieros.
- Validación con Great Expectations.
- Conversión y carga a base de datos SQLite.
- Automatización (opcional) del dashboard en Superset.
- Visualización final a través de Apache Superset.

---

## Estructura del Proyecto

```bash
.
├── ingest/
│   ├── alpha_ingest.py
│   ├── fix_and_convert_xlsx.py
│   └── csv_to_sqlite.py
├── validation/
│   └── validate_income_statement.py
├── superset/
│   ├── superset_automation.py
│   └── superset-entrypoint.sh
├── data/
│   └── *.csv
├── db/
│   └── alpha_data.db
├── doc/
│   └── Analisis Financiero Alpha Vantage.JPG
├── .env
├── docker-compose.yml
├── requirements.txt
├── requirements_automation.txt
└── README.md
```

---

## Cómo Ejecutar el Proyecto

### 1. Clonar el repositorio

```bash
git clone https://github.com/Prometean/GobiernoDatos_SB_POC.git
cd GobiernoDatos_SB_POC
```

### 2. Configurar API Key de Alpha Vantage

Editar el archivo `.env` con tu clave API personal:

```env
ALPHA_VANTAGE_API_KEY=TU_API_KEY
```

### 3. Construir e iniciar todos los servicios

```bash
docker-compose up --build
```

Esto realiza:
- Instalación de dependencias.
- Inicialización de Superset y creación de usuario admin (`admin/admin`).
- Carga de CSVs a SQLite.
- Intento de automatización de dashboard con `superset_automation.py` (opcional).

### 4. Acceder al Dashboard

Ir a: [http://localhost:8088](http://localhost:8088)  
Credenciales: `admin / admin`

---

## Dashboard en Superset

Se construyó un dashboard llamado **Análisis Financiero Alpha Vantage** con las siguientes visualizaciones:

![Dashboard](doc/Analisis%20Financiero%20Alpha%20Vantage.JPG)

1. **Revenue Timeline** – Línea temporal de ingresos anuales.
2. **Operating Cash Flow** – Flujo de caja operativo.
3. **Assets vs Liabilities** – Comparación entre activos y pasivos.
4. **Bank Overview** – Tabla con resumen financiero por banco.

---

## Componentes del Sistema

| Componente       | Descripción                                                                 |
|------------------|-----------------------------------------------------------------------------|
| `alpha_ingest.py`         | Extrae datos crudos desde Alpha Vantage.                             |
| `fix_and_convert_xlsx.py` | Limpia y convierte archivos XLSX a CSV.                              |
| `csv_to_sqlite.py`        | Carga los CSV convertidos a SQLite.                                  |
| `validate_income_statement.py` | Valida columnas clave y consistencia en `income_statement.csv`.       |
| `superset_automation.py`  | Automatiza datasets, charts y dashboard en Superset vía API.        |
| `superset-entrypoint.sh`  | Script de inicialización de Superset dentro del contenedor.          |
| `manual_guide.txt`        | Guía paso a paso para creación manual de visualizaciones (fallback). |

---

## Ejercicios Cumplidos

| Ejercicio | Descripción                                                                                      | Estado     |
|-----------|--------------------------------------------------------------------------------------------------|------------|
| 1         | Recepción y tratamiento de reportes financieros desde fuente externa (Alpha Vantage)             | ✅ Completo |
| 2         | Limpieza, transformación y validación con Great Expectations                                     | ✅ Completo |
| 3         | Diseño de estructura modular con scripts y componentes desacoplados                              | ✅ Completo |
| 4         | Creación de visualizaciones analíticas y tablero interactivo en Superset                         | ✅ Completo |

---

##  Autor

**Ean Jiménez**  
Desarrollado para la evaluación técnica de la **Superintendencia de Bancos de República Dominicana (SB)**.  
Fecha de entrega: **Junio 2025**  
Licencia: MIT

---