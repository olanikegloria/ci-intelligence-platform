FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/app ./app
COPY backend/templates ./templates
COPY fixtures ./fixtures
RUN mkdir -p /app/data
ENV PYTHONPATH=/app
ENV FIXTURES_DIR=/app/fixtures
ENV DATA_DIR=/app/data
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
