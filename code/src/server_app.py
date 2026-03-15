from flask import Flask, request, jsonify, send_from_directory
from protocols import ProvisioningServer
import binascii
import time
import requests
import os

app = Flask(__name__, static_url_path='')
server = ProvisioningServer()

# Simulators
LEGITIMATE_SIM_URL = "http://legitimate_sim:5001"

events = []
stats = {
    'total_requests': 0,
    'successful_updates': 0,
    'failed_updates': 0,
    'active_devices': set()
}

def log_event(message, type='info', device_id=None, device_type='Device', telemetry=None):
    event = {
        'timestamp': time.time(),
        'message': message,
        'type': type,
        'device_id': device_id,
        'device_type': device_type,
        'telemetry': telemetry
    }
    events.append(event)
    if len(events) > 100:
        events.pop(0)

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/api/events')
def get_events():
    return jsonify(events[-50:])

@app.route('/api/stats')
def get_stats():
    return jsonify({
        'total_requests': stats['total_requests'],
        'successful_updates': stats['successful_updates'],
        'failed_updates': stats['failed_updates'],
        'active_devices_count': len(stats['active_devices'])
    })

# --- Control API ---

@app.route('/api/control/create_device', methods=['POST'])
def control_create_device():
    try:
        requests.post(f"{LEGITIMATE_SIM_URL}/create")
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/control/trigger_update', methods=['POST'])
def control_trigger():
    device_id = request.json.get('device_id')
    try:
        requests.post(f"{LEGITIMATE_SIM_URL}/trigger/{device_id}")
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- Protocol API ---

@app.route('/enroll', methods=['POST'])
def enroll():
    data = request.json
    device_id = data.get('device_id')
    p_hex = data.get('p')
    k_root_hex = data.get('k_root')
    device_type = data.get('type', 'Device')
    
    if not all([device_id, p_hex, k_root_hex]):
        return jsonify({'error': 'Missing data'}), 400
        
    p = binascii.unhexlify(p_hex)
    k_root = binascii.unhexlify(k_root_hex)
    
    server.enroll(device_id, p, k_root)
    stats['active_devices'].add(device_id)
    
    log_event(f"Device {device_id} enrolled.", 'success', device_id, device_type)
    return jsonify({'status': 'success'})

@app.route('/update/<device_id>', methods=['GET'])
def update(device_id):
    stats['total_requests'] += 1
    try:
        firmware = b"FIRMWARE_UPDATE_V2.0"
        payload, telemetry = server.prepare_update(device_id, firmware)
        
        response = {
            'payload': {
                'P': binascii.hexlify(payload['P']).decode(),
                'N_sess': binascii.hexlify(payload['N_sess']).decode(),
                'tag': binascii.hexlify(payload['tag']).decode(),
                'ciphertext': binascii.hexlify(payload['ciphertext']).decode(),
                'counter': payload['counter']
            },
            'server_telemetry': telemetry
        }
        log_event(f"Update generated for {device_id}", 'info', device_id, telemetry=telemetry)
        return jsonify(response)
    except ValueError as e:
        stats['failed_updates'] += 1
        return jsonify({'error': str(e)}), 404

@app.route('/report', methods=['POST'])
def report():
    data = request.json
    device_id = data.get('device_id')
    message = data.get('message')
    status = data.get('status', 'info')
    device_type = data.get('type', 'Device')
    telemetry = data.get('telemetry')
    
    if status == 'success':
        stats['successful_updates'] += 1
    elif status == 'error':
        stats['failed_updates'] += 1
        
    log_event(message, status, device_id, device_type, telemetry)
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
