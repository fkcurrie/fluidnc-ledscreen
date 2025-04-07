FROM python:3.11-slim

# Set up working directory
WORKDIR /app

# Install Flask and dependencies directly
RUN pip install --no-cache-dir flask==2.3.3 werkzeug==3.0.6 gunicorn==23.0.0 jinja2==3.1.6 markupsafe==2.1.5 itsdangerous==2.1.2 click==8.1.7

# Copy application code
COPY app.py app.py
COPY templates templates/

# Mount points for system files (defined here for documentation)
VOLUME ["/proc", "/sys", "/etc"]

# Use direct command instead of gunicorn for faster startup
CMD ["python3", "app.py"] 