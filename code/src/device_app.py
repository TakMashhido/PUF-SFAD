import requests
import time
import binascii
import sys
import random
from puf import SRAMPUF
from fuzzy import FuzzyExtractor
from protocols import Device

SERVER_URL = "http://server:5000"

def report(device_id, message, status='info', device_type='Device'):
    try:
        requests.post(f"{SERVER_URL}/report", json={
            'device_id': device_id,
            'message': message,
            'status': status,
            'type': device_type
        })
    except:
        pass

def main():
    print("Initializing Device...")
    puf = SRAMPUF(size_bits=32768)
    fuzzy = FuzzyExtractor()
    device = Device(puf, fuzzy)
    
    # 1. Enroll
    print("Starting Enrollment...")
    dev_id, p, k_root = device.protocol_1_enroll()
    
    payload = {
        'device_id': dev_id,
        'p': binascii.hexlify(p).decode(),
        'k_root': binascii.hexlify(k_root).decode(),
        'type': 'Valid Device'
    }
    
    while True:
        try:
            # Wait for server to be ready
            response = requests.post(f"{SERVER_URL}/enroll", json=payload)
            if response.status_code == 200:
                print("Enrollment Successful!")
                break
        except requests.exceptions.ConnectionError:
            print("Waiting for server...")
            time.sleep(2)
    
    # Continuous Loop
    while True:
        try:
            time.sleep(random.randint(5, 15))
            print("Requesting Firmware Update...")
            report(dev_id, f"Device {dev_id} requesting update...", 'info', 'Valid Device')
            
            response = requests.get(f"{SERVER_URL}/update/{dev_id}")
            
            if response.status_code == 200:
                data = response.json()
                
                update_payload = {
                    'P': binascii.unhexlify(data['P']),
                    'N_sess': binascii.unhexlify(data['N_sess']),
                    'tag': binascii.unhexlify(data['tag']),
                    'ciphertext': binascii.unhexlify(data['ciphertext']),
                    'counter': data['counter']
                }
                
                try:
                    firmware = device.protocol_3_verify(update_payload)
                    print(f"Firmware Installed: {firmware}")
                    report(dev_id, f"Firmware verified and installed: {firmware.decode()}", 'success', 'Valid Device')
                except RuntimeError as e:
                    print(f"Verification Failed: {e}")
                    report(dev_id, f"Verification Failed: {e}", 'error', 'Valid Device')
            else:
                print(f"Update Request Failed: {response.text}")
                report(dev_id, "Update request failed on server side.", 'error', 'Valid Device')
                
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == '__main__':
    time.sleep(5)
    main()
