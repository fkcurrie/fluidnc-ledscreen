FROM python:3.9-slim

WORKDIR /app

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Create mount points for host system files
RUN mkdir -p /host/proc /host/sys /host/etc

CMD ["gunicorn", "-w", "1", "--bind", "0.0.0.0:5000", "app:app"] 