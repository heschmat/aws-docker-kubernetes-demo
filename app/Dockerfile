FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
#ENV FLASK_APP=app:app
ENV FLASK_APP=app.py

# Optional: add entrypoint script if you want auto migration on startup (skip for now)

# Add this line to fix flask shell and CLI usage
ENV PYTHONPATH=/app

CMD ["python", "app.py"]
