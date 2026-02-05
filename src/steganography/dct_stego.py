"""
DCT (Discrete Cosine Transform) Steganography module
Suitable for robust embedding (though best saved as PNG to avoid re-compression loss)
"""

import numpy as np
from PIL import Image
from scipy.fftpack import dct, idct  # type: ignore

class DCTSteganography:
    """
    Implements DCT-based steganography.
    Embeds data in the quantized DCT coefficients of the Y (Luminance) channel.
    Uses Quantization Index Modulation (QIM) for robustness against
    float->int->float conversion noise implicitly caused by saving as image pixels.
    """
    
    Q = 8  # Quantization step size. Larger = more robust, less quality. 
           # Q=8 gives robust margin against typical rounding noise.

    def __init__(self, image_path: str):
        self.image_path = image_path
        self.image = Image.open(image_path)
        
        # Crop to 8x8 blocks
        w, h = self.image.size
        new_w = w - (w % 8)
        new_h = h - (h % 8)
        if new_w != w or new_h != h:
            print(f"⚠️ Cropping image from {w}x{h} to {new_w}x{new_h} for DCT block processing")
            self.image = self.image.crop((0, 0, new_w, new_h))
            
        self.image_ycbcr = self.image.convert('YCbCr')
        self.y_array = np.array(self.image_ycbcr.split()[0], dtype=float)
        
        # Coefficients to use (ZigZag-ish order in mid-frequencies)
        # Using 8 coefficients per block allows 1 byte per block capacity
        self.coeffs = [
            (3, 1), (2, 2), (1, 3), 
            (4, 0), (3, 2), (2, 3), (1, 4), (0, 5)
        ]
        self.bits_per_block = len(self.coeffs)

    def _dct2(self, block):
        """Perform 2D DCT"""
        return dct(dct(block.T, norm='ortho').T, norm='ortho')

    def _idct2(self, block):
        """Perform 2D Inverse DCT"""
        return idct(idct(block.T, norm='ortho').T, norm='ortho')

    def calculate_capacity(self) -> int:
        """Calculate capacity in bytes"""
        h, w = self.y_array.shape
        num_blocks = (h // 8) * (w // 8)
        total_bits = num_blocks * self.bits_per_block
        # Reserve 32 bits for length
        return (total_bits - 32) // 8

    def embed(self, secret_data: bytes, output_path: str):
        """Embed bytes into chunks of standard DCT coefficients using QIM"""
        capacity = self.calculate_capacity()
        if len(secret_data) > capacity:
            raise ValueError(f"Data too large for DCT. Capacity: {capacity} bytes. Data: {len(secret_data)} bytes")

        # Prepare bits: Length (32-bit) + Data
        length_bits = format(len(secret_data), '032b')
        data_bits = ''.join(format(byte, '08b') for byte in secret_data)
        full_payload = length_bits + data_bits
        
        payload_len = len(full_payload)
        payload_idx = 0
        h, w = self.y_array.shape
        
        # Clone Y array for modification
        y_mod = self.y_array.copy()

        # Iterate over 8x8 blocks
        for i in range(0, h, 8):
            for j in range(0, w, 8):
                if payload_idx >= payload_len:
                    break
                
                # Extract block
                block = y_mod[i:i+8, j:j+8]
                dct_block = self._dct2(block)
                
                # Embed in selected coefficients
                for r, c in self.coeffs:
                    if payload_idx >= payload_len:
                        break
                    
                    bit = int(full_payload[payload_idx])
                    val = dct_block[r, c]
                    
                    # QIM Embedding
                    # Divide by Q, round to nearest integer
                    # If parity matches bit, we are good.
                    # If not, move to nearest neighbor with correct parity.
                    
                    quantized = round(val / self.Q)
                    if quantized % 2 != bit:
                        # Find nearest direction to move
                        # Check up and down
                        if val > quantized * self.Q:
                            quantized += 1 # Move up if we were already high
                        else:
                            quantized -= 1 # Move down
                            
                    # Additional check: changing quantized parity MUST change parity
                    if quantized % 2 != bit:
                        quantized += 1 # Force correct parity
                        
                    dct_block[r, c] = quantized * self.Q
                    payload_idx += 1
                
                # IDCT
                y_mod[i:i+8, j:j+8] = self._idct2(dct_block)

        # Merge and save
        y_channel = Image.fromarray(np.clip(y_mod, 0, 255).astype('uint8'), mode='L')
        _, cb, cr = self.image_ycbcr.split()
        final_img = Image.merge('YCbCr', (y_channel, cb, cr)).convert('RGB')
        
        # Save
        if output_path.lower().endswith(('.jpg', '.jpeg')):
             final_img.save(output_path, quality=100, subsampling=0)
        else:
             final_img.save(output_path)
        print(f"✅ DCT Embedding complete. Saved to {output_path}")

    def extract(self) -> bytes:
        """Extract bytes from DCT coefficients using QIM"""
        h, w = self.y_array.shape
        
        extracted_len = None
        bit_buffer = ""
        
        for i in range(0, h, 8):
            for j in range(0, w, 8):
                block = self.y_array[i:i+8, j:j+8]
                dct_block = self._dct2(block)
                
                for r, c in self.coeffs:
                    val = dct_block[r, c]
                    
                    # QIM Extract
                    quantized = round(val / self.Q)
                    bit = int(quantized) % 2
                    
                    bit_buffer += str(bit)
                    
                    # Check if we have length header
                    if extracted_len is None and len(bit_buffer) >= 32:
                        length_bits = bit_buffer[:32]
                        extracted_len = int(length_bits, 2)
                        bit_buffer = bit_buffer[32:]
                        
                        # Sanity check on length
                        if extracted_len > 100_000_000 or extracted_len < 0:
                             raise ValueError(f"Extracted invalid length: {extracted_len}. Decryption failed.")
                        
                    # Check if we have full message
                    if extracted_len is not None:

                        if len(bit_buffer) >= extracted_len * 8:
                            # We're done
                            final_bits = bit_buffer[:extracted_len * 8]
                            
                            # Convert to bytes
                            message_bytes = bytearray()
                            for k in range(0, len(final_bits), 8):
                                byte = final_bits[k:k+8]
                                message_bytes.append(int(byte, 2))
                            
                            return bytes(message_bytes)
                            
        # If we run out of blocks before finishing
        if extracted_len is None:
             raise ValueError("Could not find valid length header in DCT coefficients")
        else:
             raise ValueError(f"Incomplete message. Expected {extracted_len} bytes, found partial.")
