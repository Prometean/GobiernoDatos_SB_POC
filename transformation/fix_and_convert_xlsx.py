import pandas as pd
import os

INPUT_DIR = "data"
OUTPUT_DIR = "data/csv_fixed"
os.makedirs(OUTPUT_DIR, exist_ok=True)

for file in os.listdir(INPUT_DIR):
    if file.endswith(".xlsx"):
        try:
            df = pd.read_excel(os.path.join(INPUT_DIR, file))
            if df.empty:
                print(f"⚠️ Archivo vacío: {file}")
                continue
            # Limpia nombres de columnas
            df.columns = [str(col).strip().replace(" ", "_").replace(".", "_") for col in df.columns]
            csv_name = file.replace(".xlsx", ".csv")
            df.to_csv(os.path.join(OUTPUT_DIR, csv_name), index=False, encoding="utf-8")
            print(f"✅ Convertido: {file} -> {csv_name}")
        except Exception as e:
            print(f"❌ Error procesando {file}: {e}")
