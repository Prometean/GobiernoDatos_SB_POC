"""
Script para validar el archivo income_statement.csv usando Great Expectations.

- Verifica que existan columnas claves como totalRevenue y netIncome
- Revisa que no haya valores nulos en columnas importantes
- Asegura que totalRevenue sea un número positivo
"""

import great_expectations as ge
import pandas as pd

# Cargar el dataset desde la carpeta data
df = pd.read_csv("data/income_statement.csv")

# Convertir a dataframe de Great Expectations
df_ge = ge.from_pandas(df)

# Validaciones básicas
results = df_ge.expect_column_to_exist("totalRevenue")
print("Columna totalRevenue:", results["success"])

results = df_ge.expect_column_values_to_not_be_null("totalRevenue")
print("Sin nulos en totalRevenue:", results["success"])

results = df_ge.expect_column_values_to_be_between("totalRevenue", min_value=0, strict_min=True)
print("totalRevenue > 0:", results["success"])

results = df_ge.expect_column_to_exist("netIncome")
print("Columna netIncome:", results["success"])

results = df_ge.expect_column_values_to_not_be_null("netIncome")
print("Sin nulos en netIncome:", results["success"])
