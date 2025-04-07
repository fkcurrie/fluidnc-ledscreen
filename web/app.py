from flask import Flask, render_template, jsonify, request
import logging
import platform
import subprocess
import os
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_system_info():
    logger.info("Starting system info retrieval...")
    system_info = {
        'os': '',
        'hostname': '',
        'pi_model': '',
        'cpu_temp': '',
        'memory': '',
        'uptime': '',
        'python_version': platform.python_version()
    }
    
    try:
        # Get host OS info
        try:
            logger.info("Reading OS info...")
            with open('/etc/os-release', 'r') as f:
                os_info = dict(line.strip().split('=', 1) for line in f if '=' in line)
                system_info['os'] = os_info.get('PRETTY_NAME', '').strip('"')
                logger.info(f"OS info: {system_info['os']}")
        except Exception as e:
            logger.error(f"Error reading OS info: {e}")
            system_info['os'] = platform.platform()

        # Get hostname
        try:
            logger.info("Reading hostname...")
            with open('/etc/hostname', 'r') as f:
                system_info['hostname'] = f.read().strip()
                logger.info(f"Hostname: {system_info['hostname']}")
        except Exception as e:
            logger.error(f"Error reading hostname: {e}")
            system_info['hostname'] = platform.node()
        
        # Get Raspberry Pi model from cpuinfo
        try:
            logger.info("Reading Pi model...")
            with open('/proc/cpuinfo', 'r') as f:
                for line in f:
                    if line.startswith('Model'):
                        system_info['pi_model'] = line.split(':')[1].strip()
                        break
            # Fallback to device tree if cpuinfo doesn't have model
            if not system_info['pi_model']:
                logger.info("Falling back to device tree for Pi model...")
                with open('/proc/device-tree/model', 'r') as f:
                    system_info['pi_model'] = f.read().strip()
            logger.info(f"Pi model: {system_info['pi_model']}")
        except Exception as e:
            logger.error(f"Error reading Pi model: {e}")
            system_info['pi_model'] = 'Unknown Pi Model'
            
        # Get CPU temperature
        try:
            logger.info("Reading CPU temperature...")
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temp = float(f.read().strip()) / 1000
                system_info['cpu_temp'] = f'{temp:.1f}°C'
                logger.info(f"CPU temp: {system_info['cpu_temp']}")
        except Exception as e:
            logger.error(f"Error reading CPU temp: {e}")
            system_info['cpu_temp'] = 'N/A'
            
        # Get memory info from host
        try:
            logger.info("Reading memory info...")
            with open('/proc/meminfo', 'r') as f:
                mem_info = {}
                for line in f:
                    if ':' in line:
                        key, value = line.split(':')
                        mem_info[key.strip()] = int(value.strip().split()[0])  # Get value in kB
                mem_total = mem_info['MemTotal'] // 1024  # Convert to MB
                mem_available = mem_info['MemAvailable'] // 1024
                mem_used = mem_total - mem_available
                system_info['memory'] = f'Used: {mem_used}MB / Total: {mem_total}MB'
                logger.info(f"Memory info: {system_info['memory']}")
        except Exception as e:
            logger.error(f"Error reading memory info: {e}")
            system_info['memory'] = 'N/A'
            
        # Get uptime from host
        try:
            logger.info("Reading uptime...")
            with open('/proc/uptime', 'r') as f:
                uptime_seconds = float(f.readline().split()[0])
                days = int(uptime_seconds // 86400)
                hours = int((uptime_seconds % 86400) // 3600)
                minutes = int((uptime_seconds % 3600) // 60)
                system_info['uptime'] = f'{days}d {hours}h {minutes}m'
                logger.info(f"Uptime: {system_info['uptime']}")
        except Exception as e:
            logger.error(f"Error reading uptime: {e}")
            system_info['uptime'] = 'N/A'
            
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        
    logger.info(f"Final system info: {system_info}")
    return system_info

# Store latest state
current_state = {
    'state': 'Unknown',
    'position': {'x': 0, 'y': 0, 'z': 0},
    'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    'reconnections': 0
}

@app.route('/')
def index():
    logger.info("Rendering index page...")
    return render_template('index.html', system_info=get_system_info())

@app.route('/api/state')
def get_state():
    return jsonify(current_state)

@app.route('/api/system-info')
def get_system_info_api():
    logger.info("System info API endpoint called...")
    return jsonify(get_system_info())

@app.route('/api/update', methods=['POST'])
def update_state():
    global current_state
    try:
        current_state = request.json
        return jsonify({'status': 'success'})
    except Exception as e:
        # Log detailed error for debugging
        logger.error(f"Error updating state: {str(e)}", exc_info=True)
        # Return generic error to client
        return jsonify({'status': 'error', 'message': 'Failed to update state'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000) 