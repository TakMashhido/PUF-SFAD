import reedsolo
import os
import hashlib
from utils import sha256

class FuzzyExtractor:
    def __init__(self, n: int = 255, t: int = 30, repetition: int = 15):
        """
        Initialize Fuzzy Extractor with Concatenated Code (Repetition + RS).
        
        Args:
            n: RS Block size in bytes (usually 255).
            t: RS Error correction capability in bytes (symbols).
            repetition: Repetition factor (must be odd). Higher = more noise tolerance.
                        For 15% BER, we need strong reduction. 
                        Rep(15) reduces 15% BER to ~0.003% BER, which RS can handle easily.
        """
                  
        self.n = n
        self.t = t
        self.n_parity = 2 * t
        self.rsc = reedsolo.RSCodec(self.n_parity)
        
        self.repetition = repetition
        if self.repetition % 2 == 0:
            self.repetition += 1
            
                                  
        self.k = self.n - self.n_parity
        
                    
        self.n_bytes = self.n
        self.k_bytes = self.k
        
                                     
                                               
        self.needed_bits = self.n_bytes * 8 * self.repetition
        self.needed_bytes = (self.needed_bits + 7) // 8

    def _majority_vote(self, w: bytes) -> bytes:
        """Apply repetition decoding (majority vote)."""
                               
                                                  
                                                          
        
                                                                       
        if self.repetition == 1:
            return w

        bits = []
        for b in w:
            for i in range(8):
                bits.append((b >> (7-i)) & 1)
        
              
        voted_bits = []
        target_bits = self.n_bytes * 8
        
                                               
        if len(bits) < target_bits * self.repetition:
            raise ValueError(f"Not enough bits. Have {len(bits)}, need {target_bits * self.repetition}")

        for i in range(target_bits):
            chunk_start = i * self.repetition
            chunk = bits[chunk_start : chunk_start + self.repetition]
            
                           
            ones = sum(chunk)
            if ones > self.repetition // 2:
                voted_bits.append(1)
            else:
                voted_bits.append(0)
                
                               
        voted_bytes = bytearray()
        for i in range(0, len(voted_bits), 8):
            byte_val = 0
            for j in range(8):
                if i+j < len(voted_bits):
                    byte_val |= (voted_bits[i+j] << (7-j))
            voted_bytes.append(byte_val)
            
        return bytes(voted_bytes)

    def gen(self, w: bytes) -> tuple[bytes, bytes]:
        """
        Enrollment Phase: Gen(w) -> (K, P)
        """
        if len(w) < self.needed_bytes:
            raise ValueError(f"Input w too short. Need {self.needed_bytes} bytes for repetition={self.repetition}.")
            
                                                           
                                                                
                                 
                                                                       
                                                                        
                                                                             
                                                                                
                                             
          
                                                                                 
                                                   
                                                            
                               
         
                         
                                                                                                           
                                                     
                                                            
                                     
        
                                                          
        
                                 
        data = os.urandom(self.k_bytes)
        
                      
        rs_codeword = self.rsc.encode(data)                 
        
                                            
                                                                   
        expanded_bits = []
        for b in rs_codeword:
            for i in range(8):
                bit = (b >> (7-i)) & 1
                expanded_bits.extend([bit] * self.repetition)
                
                                        
                                                      
        c_expanded = bytearray()
        current_byte = 0
        bit_count = 0
        for b in expanded_bits:
            current_byte = (current_byte << 1) | b
            bit_count += 1
            if bit_count == 8:
                c_expanded.append(current_byte)
                current_byte = 0
                bit_count = 0
        if bit_count > 0:
            c_expanded.append(current_byte << (8-bit_count))
            
        c_expanded = bytes(c_expanded)
        
                                                     
                                            
        if len(w) < len(c_expanded):
             raise ValueError(f"w too short. Need {len(c_expanded)}")
             
        p = bytearray(len(c_expanded))
        for i in range(len(c_expanded)):
            p[i] = w[i] ^ c_expanded[i]
            
        p = bytes(p)
        
                       
        k = sha256(rs_codeword)
        
        return k, p

    def rep(self, w_prime: bytes, p: bytes) -> bytes:
        """
        Reconstruction Phase: Rep(w', P) -> K
        """
        if len(w_prime) < len(p):
             raise ValueError(f"Input w' too short.")
             
        w_prime = w_prime[:len(p)]
        
                                            
                                     
        c_expanded_prime = bytearray(len(p))
        for i in range(len(p)):
            c_expanded_prime[i] = w_prime[i] ^ p[i]
            
        c_expanded_prime = bytes(c_expanded_prime)
        
                                              
                                                                                
        
                               
        bits = []
        for b in c_expanded_prime:
            for i in range(8):
                bits.append((b >> (7-i)) & 1)
                
        recovered_bits = []
                                                              
        target_bits = self.n_bytes * 8
        
        for i in range(target_bits):
            chunk_start = i * self.repetition
            if chunk_start + self.repetition > len(bits):
                break
            chunk = bits[chunk_start : chunk_start + self.repetition]
            if sum(chunk) > self.repetition // 2:
                recovered_bits.append(1)
            else:
                recovered_bits.append(0)
                
                                                       
        c_prime = bytearray()
        current_byte = 0
        bit_count = 0
        for b in recovered_bits:
            current_byte = (current_byte << 1) | b
            bit_count += 1
            if bit_count == 8:
                c_prime.append(current_byte)
                current_byte = 0
                bit_count = 0
        
        c_prime = bytes(c_prime)
        
                      
        try:
            decoded_data, decoded_msg_with_ecc, err_list = self.rsc.decode(c_prime)
            corrected_codeword = decoded_msg_with_ecc
            k = sha256(corrected_codeword)
            return k
        except reedsolo.ReedSolomonError:
            return None
