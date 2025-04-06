# Use the official Python image as a parent image
FROM python:3.11-slim AS builder

# Install build dependencies
# Added gcc, g++, make, git
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-dev \
    build-essential \
    gcc g++ make \
    libavahi-compat-libdnssd-dev \
    python3-ifaddr \
    git \
 && rm -rf /var/lib/apt/lists/*

# Set environment variables for pip
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /opt/build

# Create a virtual environment
RUN python3 -m venv /opt/venv

# Copy requirements file
COPY requirements.txt .

# Install dependencies into the virtual environment
# Let pip try to build ifaddr if needed
RUN /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# --- Final Stage ---
FROM python:3.11-slim AS final

# Set environment variables for locale (good practice)
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

# Install runtime dependencies + wget (remove fontforge/fontconfig)
RUN apt-get update && apt-get install -y --no-install-recommends \
    sudo \
    libgpiod2 \
    libatlas-base-dev \
    fonts-terminus \
    fonts-dejavu-core \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user 'appuser'
RUN useradd -m -s /bin/bash appuser && \
    echo "appuser ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

# Copy the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Create fonts directory and download fonts as root
RUN mkdir -p /app/fonts && \
    BDF_BASE_URL="https://raw.githubusercontent.com/hzeller/rpi-rgb-led-matrix/master/fonts" && \
    cd /app/fonts && \
    wget "$BDF_BASE_URL/4x6.bdf" && \
    wget "$BDF_BASE_URL/5x7.bdf" && \
    wget "$BDF_BASE_URL/5x8.bdf" && \
    wget "$BDF_BASE_URL/6x10.bdf" && \
    wget "$BDF_BASE_URL/6x12.bdf" && \
    ls -l /app/fonts # Verify downloads

WORKDIR /app

# Copy application code and configuration LATER - these change more often
COPY fluidnc_monitor.py monitor.py logging_config.py ./
COPY config ./config

# Ensure the app directory (including fonts) and venv are owned by appuser
RUN chown -R appuser:appuser /app && \
    chown -R appuser:appuser /opt/venv

USER appuser

# Set the entrypoint to use the virtual environment's Python
ENV PATH="/opt/venv/bin:$PATH"

CMD ["python", "monitor.py"] 