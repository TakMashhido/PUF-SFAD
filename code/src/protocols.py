import os
from puf import SRAMPUF
from fuzzy import FuzzyExtractor
from utils import sha256, hkdf_derive, aes_gcm_encrypt, aes_gcm_decrypt

class ProvisioningServer:
    def __init__(self):
        self.db = {}                                      

    def enroll(self, device_id: str, p: bytes, k_root: bytes):
        """Protocol 1 (Server side): Store enrollment data."""
        self.db[device_id] = {'P': p, 'K_root': k_root, 'counter': 0}

    def prepare_update(self, device_id: str, firmware: bytes) -> dict:
        """
        Protocol 2: Cryptographic Binding & Distribution.
        
        Args:
            device_id: Target device ID.
            firmware: Plaintext firmware image.
            
        Returns:
            Payload dictionary containing {header, P, nonce, tag, ciphertext}.
        """
        record = self.db.get(device_id)
        if not record:
            raise ValueError(f"Device {device_id} not found.")
            
        p = record['P']
        k_root = record['K_root']
        current_counter = record['counter']
        new_counter = current_counter + 1
        
                   
        record['counter'] = new_counter
        
                                   
        n_sess = os.urandom(12)
        
                               
                                                
        k_sess = hkdf_derive(ikm=k_root, salt=n_sess)
        
                             
                                      
        iv, ciphertext, tag = aes_gcm_encrypt(k_sess, firmware, nonce=n_sess)
        
                              
        payload = {
            'P': p,
            'N_sess': n_sess,
            'tag': tag,
            'ciphertext': ciphertext,
            'counter': new_counter
        }

        # Telemetry for UI
        telemetry = {
            'k_root_hash': sha256(k_root).hex(),
            'k_sess': k_sess.hex(),
            'n_sess': n_sess.hex(),
            'iv': iv.hex(),
            'ciphertext': ciphertext.hex(),
            'tag': tag.hex()
        }
        
        return payload, telemetry

class Device:
    def __init__(self, puf: SRAMPUF, fuzzy: FuzzyExtractor):
        self.puf = puf
        self.fuzzy = fuzzy
        self.id = os.urandom(4).hex()
        self.k_root = None                         
        self.counter = 0                                          

    def protocol_1_enroll(self) -> tuple[str, bytes, bytes]:
        """
        Protocol 1 (Device side): Generate P and K_root.
        """
                                                 
        w = self.puf.power_up(noise_factor=0.0)                    
        
                             
        k_root, p = self.fuzzy.gen(w)
        
                                           
        return self.id, p, k_root

    def protocol_3_verify(self, payload: dict) -> bytes:
        """
        Protocol 3: On-Device Reconstruction & Verification.
        
        Args:
            payload: The update package.
            
        Returns:
            Decrypted firmware bytes.
        """
        p = payload['P']
        n_sess = payload['N_sess']
        tag = payload['tag']
        ciphertext = payload['ciphertext']
        msg_counter = payload.get('counter', 0)
        
                         
        if msg_counter <= self.counter:
            raise RuntimeError(f"Replay Detected! Msg Counter {msg_counter} <= Device Counter {self.counter}")
        
                                             
                                 
        w_prime = self.puf.power_up(noise_factor=1.0)
        
                                 
        k_root = self.fuzzy.rep(w_prime, p)
        
        if k_root is None:
            raise RuntimeError("PUF Reconstruction Failed (Tamper/Noise)")
            
                               
        k_sess = hkdf_derive(ikm=k_root, salt=n_sess)
        
                    
        try:
            firmware = aes_gcm_decrypt(k_sess, n_sess, ciphertext, tag)
                                            
            self.counter = msg_counter
            
            telemetry = {
                'reconstructed_k_root_hash': sha256(k_root).hex(),
                'derived_k_sess': k_sess.hex(),
                'decrypted_firmware': firmware.decode()
            }
            return firmware, telemetry
        except Exception as e:
            raise RuntimeError("Cryptographic Integrity Failure") from e
