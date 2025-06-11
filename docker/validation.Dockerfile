FROM python:3.10-slim

WORKDIR /app

# Copiar script y datos desde el contexto del build
COPY validation/validate_income_statement.py .
COPY data/ ./data/

RUN pip install --no-cache-dir pandas great_expectations

CMD ["python", "validate_income_statement.py"]
