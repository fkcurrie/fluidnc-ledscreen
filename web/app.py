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
            with open('/host/etc/os-release', 'r') as f:
                os_info = dict(line.strip().split('=', 1) for line in f if '=' in line)
                system_info['os'] = os_info.get('PRETTY_NAME', '').strip('"')
        except:
            system_info['os'] = platform.platform()

        # Get hostname
        try:
            with open('/host/etc/hostname', 'r') as f:
                system_info['hostname'] = f.read().strip()
        except:
            system_info['hostname'] = platform.node()
        
        # Get Raspberry Pi model from cpuinfo
        try:
            with open('/host/proc/cpuinfo', 'r') as f:
                for line in f:
                    if line.startswith('Model'):
                        system_info['pi_model'] = line.split(':')[1].strip()
                        break
            # Fallback to device tree if cpuinfo doesn't have model
            if not system_info['pi_model']:
                with open('/host/proc/device-tree/model', 'r') as f:
                    system_info['pi_model'] = f.read().strip()
        except:
            system_info['pi_model'] = 'Unknown Pi Model'
            
        # Get CPU temperature
        try:
            with open('/host/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temp = float(f.read().strip()) / 1000
                system_info['cpu_temp'] = f'{temp:.1f}°C'
        except:
            system_info['cpu_temp'] = 'N/A'
            
        # Get memory info from host
        try:
            with open('/host/proc/meminfo', 'r') as f:
                mem_info = {}
                for line in f:
                    if ':' in line:
                        key, value = line.split(':')
                        mem_info[key.strip()] = int(value.strip().split()[0])  # Get value in kB
                mem_total = mem_info['MemTotal'] // 1024  # Convert to MB
                mem_available = mem_info['MemAvailable'] // 1024
                mem_used = mem_total - mem_available
                system_info['memory'] = f'Used: {mem_used}MB / Total: {mem_total}MB'
        except:
            system_info['memory'] = 'N/A'
            
        # Get uptime from host
        try:
            with open('/host/proc/uptime', 'r') as f:
                uptime_seconds = float(f.readline().split()[0])
                days = int(uptime_seconds // 86400)
                hours = int((uptime_seconds % 86400) // 3600)
                minutes = int((uptime_seconds % 3600) // 60)
                system_info['uptime'] = f'{days}d {hours}h {minutes}m'
        except:
            system_info['uptime'] = 'N/A'
            
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        
    return system_info

# Store latest state
current_state = {
    'state': 'Unknown',
    'position': {'x': 0.0, 'y': 0.0, 'z': 0.0},
    'time': '',
    'reconnections': 0
}

@app.route('/')
def index():
    return render_template('index.html', system_info=get_system_info())

@app.route('/api/state', methods=['GET'])
def get_state():
    return jsonify(current_state)

@app.route('/api/state', methods=['POST'])
def update_state():
    global current_state
    try:
        data = request.get_json()
        logger.info(f"Received update: {data}")
        
        if not data or 'state' not in data:
            logger.error("Invalid data received")
            return jsonify({"status": "error", "message": "Invalid data"}), 400
            
        current_state = data
        return jsonify({"status": "ok"})
    except Exception as e:
        logger.error(f"Error processing update: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000) 