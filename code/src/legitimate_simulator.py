from flask import Flask, request, jsonify
import threading
import time
import requests
import binascii
import random
from puf import SRAMPUF
from fuzzy import FuzzyExtractor
from protocols import Device

app = Flask(__name__)

SERVER_URL = "http://server:5000"
devices = {} # id -> {device_obj, thread, running}

class DeviceThread(threading.Thread):
    def __init__(self, device_id, puf_size=32768):
        super().__init__()
        self.device_id = device_id
        self.puf = SRAMPUF(size_bits=puf_size)
        self.fuzzy = FuzzyExtractor()
        self.device = Device(self.puf, self.fuzzy)
        self.running = True
        self.trigger_update = False
        
    def run(self):
        # Enrollment
        dev_id, p, k_root = self.device.protocol_1_enroll()
        self.real_id = dev_id 
        
        payload = {
            'device_id': dev_id,
            'p': binascii.hexlify(p).decode(),
            'k_root': binascii.hexlify(k_root).decode(),
            'type': 'Valid Device'
        }
        
        # Register with Server
        while self.running:
            try:
                requests.post(f"{SERVER_URL}/enroll", json=payload)
                break
            except:
                time.sleep(2)
        
        # Main Loop (Manual Only)
        while self.running:
            if self.trigger_update:
                self.perform_update()
                self.trigger_update = False
            time.sleep(0.1)

    def perform_update(self):
        try:
            report(self.real_id, f"Requesting update...", 'info')
            response = requests.get(f"{SERVER_URL}/update/{self.real_id}")
            
            if response.status_code == 200:
                data = response.json()
                payload = data['payload']
                
                update_payload = {
                    'P': binascii.unhexlify(payload['P']),
                    'N_sess': binascii.unhexlify(payload['N_sess']),
                    'tag': binascii.unhexlify(payload['tag']),
                    'ciphertext': binascii.unhexlify(payload['ciphertext']),
                    'counter': payload['counter']
                }
                
                try:
                    firmware, telemetry = self.device.protocol_3_verify(update_payload)
                    report(self.real_id, f"Update Installed. FW: {firmware.decode()}", 'success', telemetry)
                except RuntimeError as e:
                    report(self.real_id, f"Verification Failed: {e}", 'error')
            else:
                report(self.real_id, "Update request failed.", 'error')
        except Exception as e:
            print(f"Device Error: {e}")

def report(device_id, message, status, telemetry=None):
    try:
        requests.post(f"{SERVER_URL}/report", json={
            'device_id': device_id,
            'message': message,
            'status': status,
            'type': 'Valid Device',
            'telemetry': telemetry
        })
    except:
        pass

@app.route('/create', methods=['POST'])
def create_device():
    thread = DeviceThread(None)
    thread.start()
    return jsonify({'status': 'started'})

@app.route('/trigger/<device_id>', methods=['POST'])
def trigger(device_id):
    for thread in threading.enumerate():
        if isinstance(thread, DeviceThread) and getattr(thread, 'real_id', None) == device_id:
            thread.trigger_update = True
            return jsonify({'status': 'triggered'})
    return jsonify({'error': 'device not found'}), 404

if __name__ == '__main__':
    # Auto-start one device for immediate activity
    t = DeviceThread(None)
    t.start()
    app.run(host='0.0.0.0', port=5001)
