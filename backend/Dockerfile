FROM python:3.12-slim

WORKDIR /code

COPY requirements.txt requirements-dev.txt ./
# В dev-образе ставим вместе с pytest и т.п. Для прода был бы отдельный stage.
RUN pip install --no-cache-dir -r requirements-dev.txt

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
