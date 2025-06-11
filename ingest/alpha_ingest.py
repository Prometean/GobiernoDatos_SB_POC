import os
import requests
import pandas as pd

API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
BASE_URL = "https://www.alphavantage.co/query"
SYMBOL = "WFC"
OUTPUT_DIR = "../data"

endpoints = {
    "income_statement": "INCOME_STATEMENT",
    "balance_sheet": "BALANCE_SHEET",
    "cash_flow": "CASH_FLOW",
    "overview": "OVERVIEW"
}

for name, function in endpoints.items():
    params = {
        "function": function,
        "symbol": SYMBOL,
        "apikey": API_KEY
    }
    response = requests.get(BASE_URL, params=params)
    if response.status_code == 200:
        data = response.json()
        if "annualReports" in data:
            df = pd.DataFrame(data["annualReports"])
        elif "quarterlyReports" in data:
            df = pd.DataFrame(data["quarterlyReports"])
        else:
            df = pd.DataFrame([data])
        csv_path = os.path.join(OUTPUT_DIR, f"{name}.csv")
        df.to_csv(csv_path, index=False)
        print(f"{name} guardado en {csv_path}")
    else:
        print(f"Error al obtener {name}: {response.status_code}")
