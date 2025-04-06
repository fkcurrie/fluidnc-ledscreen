FROM python:3.11-slim

# Set up working directory
WORKDIR /app

# Install Flask and dependencies directly
RUN pip install --no-cache-dir flask==1.1.2 werkzeug==1.0.1 gunicorn==20.1.0 jinja2==2.11.3 markupsafe==2.0.1 itsdangerous==1.1.0 click==7.1.2

# Copy application code
COPY web/app.py app.py
COPY web/templates templates/

# Mount points for system files (defined here for documentation)
VOLUME ["/proc", "/sys", "/etc"]

# Use direct command instead of gunicorn for faster startup
CMD ["python3", "app.py"] 