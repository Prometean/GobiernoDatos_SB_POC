# transformation/csv_to_sqlite.py
import pandas as pd
import os
import sqlite3

CSV_DIR = "data"
DB_PATH = "db/alpha_data.db"

conn = sqlite3.connect(DB_PATH)

for file in os.listdir(CSV_DIR):
    if file.endswith(".csv"):
        df = pd.read_csv(os.path.join(CSV_DIR, file))
        table_name = file.replace(".csv", "")
        df.to_sql(table_name, conn, if_exists="replace", index=False)
        print(f"✅ Guardado en SQLite: {table_name}")

conn.close()
