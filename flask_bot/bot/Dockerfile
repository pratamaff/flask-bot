FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot_service.py .

CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:8000", "bot_service:app"]
