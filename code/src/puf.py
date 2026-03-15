import numpy as np
import os

class SRAMPUF:
    def __init__(self, size_bits: int = 256, sigma_p: float = 0.05, sigma_n: float = 0.02):
        """
        Initialize SRAM PUF instance.
        
        Args:
            size_bits: Number of bits in the PUF response.
            sigma_p: Process variation standard deviation (inter-device).
            sigma_n: Noise standard deviation (intra-device).
        """
        self.size_bits = size_bits
        self.sigma_p = sigma_p
        self.sigma_n = sigma_n
        
                                                               
                                                          
                                                   
                                            
        self.fingerprint = np.random.normal(0, self.sigma_p, size_bits)

    def power_up(self, noise_factor: float = 1.0) -> bytes:
        """
        Simulate a power-up event and return the SRAM startup pattern.
        
        Args:
            noise_factor: Multiplier for noise (to simulate temp/voltage stress).
        
        Returns:
            bytes: The noisy PUF response.
        """
                                                         
        noise = np.random.normal(0, self.sigma_n * noise_factor, self.size_bits)
        
                                                          
        effective_mismatch = self.fingerprint + noise
        
                                       
        bits = (effective_mismatch > 0).astype(int)
        
                              
                                                                           
        if self.size_bits % 8 != 0:
            raise ValueError("PUF size must be multiple of 8")
            
        byte_array = np.packbits(bits)
        return bytes(byte_array)


def calculate_ber(ref: bytes, noisy: bytes) -> float:
    """Calculate Bit Error Rate between two byte strings."""
    if len(ref) != len(noisy):
        raise ValueError("Inputs must have same length")
    
    diff_bits = 0
    total_bits = len(ref) * 8
    
    for b1, b2 in zip(ref, noisy):
        xor_val = b1 ^ b2
        diff_bits += bin(xor_val).count('1')
        
    return diff_bits / total_bits
