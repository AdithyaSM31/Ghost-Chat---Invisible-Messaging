"""
LSB (Least Significant Bit) Steganography for PNG images
Simple but effective for uncompressed images
"""

from PIL import Image
import numpy as np
from pathlib import Path


class LSBSteganography:
    """Hide data in image using LSB technique"""
    
    def __init__(self, image_path: str):
        """
        Initialize with cover image
        
        Args:
            image_path: Path to cover image (PNG recommended)
        """
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        self.image = Image.open(image_path)
        self.image = self.image.convert('RGB')  # Ensure RGB mode
        self.width, self.height = self.image.size
        
        # Store original image path for reference
        self.image_path = image_path
    
    def calculate_capacity(self) -> int:
        """
        Calculate maximum data capacity in bytes
        
        The capacity depends on:
        - Image dimensions (width × height)
        - Number of color channels (3 for RGB)
        - 1 bit per channel (LSB)
        - 32 bits reserved for length encoding
        
        Returns:
            Maximum bytes that can be hidden
        """
        # Each pixel has 3 channels (R, G, B)
        # We can hide 1 bit in each channel
        total_bits = self.width * self.height * 3
        
        # Reserve 32 bits for length encoding
        usable_bits = total_bits - 32
        
        return usable_bits // 8
    
    def embed(self, secret_data: bytes, output_path: str):
        """
        Hide secret data in image using LSB technique
        
        Algorithm:
        1. Flatten image into 1D array of pixel values
        2. Encode data length in first 32 bits
        3. Replace LSB of each pixel value with data bits
        4. Reshape and save as stego image
        
        Args:
            secret_data: Binary data to hide
            output_path: Where to save stego image
            
        Raises:
            ValueError: If data is too large for image
        """
        # Check capacity
        max_capacity = self.calculate_capacity()
        if len(secret_data) > max_capacity:
            raise ValueError(
                f"Data too large! Max capacity: {max_capacity} bytes "
                f"({max_capacity / 1024:.2f} KB), "
                f"Data size: {len(secret_data)} bytes "
                f"({len(secret_data) / 1024:.2f} KB)"
            )
        
        # Convert image to numpy array
        img_array = np.array(self.image)
        flat_img = img_array.flatten()
        
        # Convert data to binary string
        data_len = len(secret_data)
        data_binary = ''.join(format(byte, '08b') for byte in secret_data)
        
        # Encode length in first 32 bits (supports up to 4GB, practically limited by image size)
        length_binary = format(data_len, '032b')
        
        # Embed length in first 32 pixels
        for i in range(32):
            # Clear LSB and set to length bit
            flat_img[i] = (flat_img[i] & 0xFE) | int(length_binary[i])
        
        # Embed data bits starting from position 32
        for i, bit in enumerate(data_binary):
            # Clear LSB and set to data bit
            flat_img[32 + i] = (flat_img[32 + i] & 0xFE) | int(bit)
        
        # Reshape back to original image dimensions
        stego_array = flat_img.reshape(img_array.shape)
        
        # Create and save stego image
        stego_image = Image.fromarray(stego_array.astype('uint8'), 'RGB')
        
        # Ensure output path is valid
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save as PNG to preserve data (JPEG would lose it due to compression)
        if output_path.suffix.lower() != '.png':
            output_path = output_path.with_suffix('.png')
        
        stego_image.save(output_path, 'PNG')
        
        print(f"✅ Hidden {data_len} bytes ({data_len / 1024:.2f} KB) in {output_path.name}")
        print(f"   Capacity used: {data_len / max_capacity * 100:.2f}%")
    
    def extract(self, stego_image_path: str = None) -> bytes:
        """
        Extract hidden data from stego image
        
        Algorithm:
        1. Load stego image and flatten
        2. Extract length from first 32 bits
        3. Extract data bits from subsequent pixels
        4. Convert binary back to bytes
        
        Args:
            stego_image_path: Path to stego image (if None, uses initialized image)
            
        Returns:
            Extracted binary data
            
        Raises:
            ValueError: If extracted length is invalid
        """
        # Load stego image
        if stego_image_path:
            stego_img = Image.open(stego_image_path).convert('RGB')
        else:
            stego_img = self.image
        
        stego_array = np.array(stego_img)
        flat_img = stego_array.flatten()
        
        # Extract length from first 32 bits
        length_binary = ''.join(str(flat_img[i] & 1) for i in range(32))
        data_len = int(length_binary, 2)
        
        # Validate length
        max_capacity = self.calculate_capacity()
        if data_len > max_capacity or data_len < 0:
            raise ValueError(
                f"Invalid data length in image: {data_len} bytes. "
                f"Maximum capacity is {max_capacity} bytes. "
                f"The image may not contain hidden data or is corrupted."
            )
        
        # Extract data bits
        data_binary = ''.join(
            str(flat_img[32 + i] & 1) 
            for i in range(data_len * 8)
        )
        
        # Convert binary string to bytes
        extracted_data = bytearray()
        for i in range(0, len(data_binary), 8):
            byte_str = data_binary[i:i+8]
            extracted_data.append(int(byte_str, 2))
        
        print(f"✅ Extracted {data_len} bytes ({data_len / 1024:.2f} KB)")
        return bytes(extracted_data)
    
    def get_info(self) -> dict:
        """
        Get information about the image
        
        Returns:
            Dictionary with image information
        """
        capacity = self.calculate_capacity()
        return {
            'path': str(self.image_path),
            'width': self.width,
            'height': self.height,
            'mode': self.image.mode,
            'total_pixels': self.width * self.height,
            'capacity_bytes': capacity,
            'capacity_kb': capacity / 1024,
            'capacity_mb': capacity / (1024 * 1024)
        }


# Self-test function
def _test():
    """Test the LSB steganography module"""
    print("Testing LSBSteganography...")
    print("\nNote: This test requires a test image.")
    print("Creating a test image...")
    
    # Create a test image
    test_img = Image.new('RGB', (800, 600), color=(100, 150, 200))
    test_path = Path('test_image.png')
    test_img.save(test_path)
    print(f"✅ Created test image: {test_path}")
    
    # Initialize steganography with test image
    stego = LSBSteganography(str(test_path))
    
    # Display info
    info = stego.get_info()
    print(f"\nImage Info:")
    print(f"  Dimensions: {info['width']}x{info['height']}")
    print(f"  Total Pixels: {info['total_pixels']:,}")
    print(f"  Capacity: {info['capacity_kb']:.2f} KB ({info['capacity_bytes']:,} bytes)")
    
    # Test data
    secret_message = b"This is a secret message hidden using LSB steganography! " * 10
    print(f"\nSecret data size: {len(secret_message)} bytes")
    
    # Embed
    print("\nEmbedding data...")
    output_path = 'test_stego.png'
    stego.embed(secret_message, output_path)
    
    # Extract
    print("\nExtracting data...")
    extracted = stego.extract(output_path)
    
    # Verify
    if extracted == secret_message:
        print("✅ LSB Steganography module working correctly!")
        print(f"   Successfully embedded and extracted {len(secret_message)} bytes")
    else:
        print("❌ Error: Extracted data doesn't match original!")
    
    # Cleanup
    test_path.unlink()
    Path(output_path).unlink()
    print("\n🧹 Cleaned up test files")


if __name__ == "__main__":
    _test()
