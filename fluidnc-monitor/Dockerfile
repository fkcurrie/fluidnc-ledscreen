FROM fluidnc-ledscreen-base:latest

# Copy application files
COPY --chown=monitoruser:monitoruser ../fluidnc_monitor.py monitor.py
COPY --chown=monitoruser:monitoruser ../logging_config.py logging_config.py
COPY --chown=monitoruser:monitoruser ../config config/

CMD ["python3", "monitor.py"]
