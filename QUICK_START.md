# Quick Start Implementation Guide
## Get Your Ghost Chat Project Running in 1 Hour

---

## 🚀 Rapid Prototyping Path

This guide helps you build a **minimal working prototype** quickly, then expand it.

---

## Step 1: Environment Setup (5 minutes)

### Create Project Structure
```bash
# Navigate to your project directory
cd "c:\Users\adith\Downloads\Cryptography and Network Security\Project"

# Create basic structure
mkdir src
mkdir src\crypto
mkdir src\steganography
mkdir tests
mkdir data
mkdir data\cover_images
mkdir data\stego_output
```

### Install Dependencies
```bash
# Create requirements.txt
pip install pycryptodome Pillow numpy scipy scikit-image
```

---

## Step 2: Basic Encryption (15 minutes)

### Create `src/crypto/encryption.py`

```python
"""
AES-256-GCM encryption module for Ghost Chat
"""

from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Random import get_random_bytes
import base64


class MessageEncryptor:
    """Handles message encryption and decryption using AES-256-GCM"""
    
    def __init__(self, password: str):
        """
        Initialize encryptor with password
        
        Args:
            password: User password for key derivation
        """
        self.password = password
    
    def encrypt(self, plaintext: str) -> dict:
        """
        Encrypt plaintext message
        
        Args:
            plaintext: Message to encrypt
            
        Returns:
            Dictionary containing salt, nonce, ciphertext, and tag
        """
        # Generate random salt for key derivation
        salt = get_random_bytes(32)
        
        # Derive encryption key from password using PBKDF2
        key = PBKDF2(self.password, salt, dkLen=32, count=100000)
        
        # Create AES cipher in GCM mode (authenticated encryption)
        cipher = AES.new(key, AES.MODE_GCM)
        
        # Encrypt and generate authentication tag
        ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode('utf-8'))
        
        return {
            'salt': salt,
            'nonce': cipher.nonce,
            'ciphertext': ciphertext,
            'tag': tag
        }
    
    def decrypt(self, encrypted_data: dict) -> str:
        """
        Decrypt ciphertext
        
        Args:
            encrypted_data: Dictionary with salt, nonce, ciphertext, tag
            
        Returns:
            Decrypted plaintext message
        """
        # Derive same key from password and salt
        key = PBKDF2(
            self.password, 
            encrypted_data['salt'], 
            dkLen=32, 
            count=100000
        )
        
        # Create cipher with saved nonce
        cipher = AES.new(key, AES.MODE_GCM, nonce=encrypted_data['nonce'])
        
        # Decrypt and verify authentication tag
        try:
            plaintext = cipher.decrypt_and_verify(
                encrypted_data['ciphertext'], 
                encrypted_data['tag']
            )
            return plaintext.decode('utf-8')
        except ValueError:
            raise ValueError("Decryption failed: wrong password or corrupted data")


# Quick test
if __name__ == "__main__":
    encryptor = MessageEncryptor("MySecurePassword123!")
    
    message = "This is a secret message!"
    print(f"Original: {message}")
    
    # Encrypt
    encrypted = encryptor.encrypt(message)
    print(f"Encrypted: {encrypted['ciphertext'][:20]}... (showing first 20 bytes)")
    
    # Decrypt
    decrypted = encryptor.decrypt(encrypted)
    print(f"Decrypted: {decrypted}")
    
    assert message == decrypted, "Encryption/Decryption failed!"
    print("✅ Encryption module working correctly!")
```

### Test It
```bash
cd src/crypto
python encryption.py
```

---

## Step 3: Message Protocol (10 minutes)

### Create `src/protocol/ghost_protocol.py`

```python
"""
Ghost Chat message protocol for structured payload
"""

import struct


class GhostProtocol:
    """Handles message packing and unpacking"""
    
    # Protocol constants
    MAGIC = b'GHST'  # Magic number to identify Ghost messages
    VERSION = 1       # Protocol version
    HEADER_SIZE = 64  # Fixed header size
    TAG_SIZE = 16     # GCM authentication tag size
    
    @staticmethod
    def pack(encrypted_data: dict) -> bytes:
        """
        Pack encrypted data into protocol format
        
        Format:
        - Magic (4 bytes): 'GHST'
        - Version (2 bytes): Protocol version
        - Payload length (4 bytes): Ciphertext length
        - Salt (32 bytes): For key derivation
        - Nonce (12 bytes): For AES-GCM
        - Reserved (10 bytes): Future use
        - Ciphertext (variable): Encrypted message
        - Tag (16 bytes): Authentication tag
        
        Args:
            encrypted_data: Dictionary from MessageEncryptor.encrypt()
            
        Returns:
            Packed binary message
        """
        # Extract components
        salt = encrypted_data['salt']
        nonce = encrypted_data['nonce']
        ciphertext = encrypted_data['ciphertext']
        tag = encrypted_data['tag']
        
        # Build header
        header = struct.pack(
            '!4sHI32s12s10s',
            GhostProtocol.MAGIC,           # Magic number
            GhostProtocol.VERSION,         # Version
            len(ciphertext),                # Payload length
            salt,                           # Salt (32 bytes)
            nonce,                          # Nonce (12 bytes)
            b'\x00' * 10                   # Reserved (10 bytes)
        )
        
        # Concatenate: header + ciphertext + tag
        return header + ciphertext + tag
    
    @staticmethod
    def unpack(packed_message: bytes) -> dict:
        """
        Unpack protocol message
        
        Args:
            packed_message: Binary message from pack()
            
        Returns:
            Dictionary with salt, nonce, ciphertext, tag
        """
        # Validate minimum length
        if len(packed_message) < GhostProtocol.HEADER_SIZE + GhostProtocol.TAG_SIZE:
            raise ValueError("Message too short to be valid Ghost protocol")
        
        # Unpack header
        header_data = struct.unpack(
            '!4sHI32s12s10s',
            packed_message[:GhostProtocol.HEADER_SIZE]
        )
        
        magic, version, payload_len, salt, nonce, _ = header_data
        
        # Validate magic number
        if magic != GhostProtocol.MAGIC:
            raise ValueError(f"Invalid magic number: {magic}")
        
        # Validate version
        if version != GhostProtocol.VERSION:
            raise ValueError(f"Unsupported protocol version: {version}")
        
        # Extract ciphertext and tag
        ciphertext_start = GhostProtocol.HEADER_SIZE
        ciphertext_end = ciphertext_start + payload_len
        tag_end = ciphertext_end + GhostProtocol.TAG_SIZE
        
        ciphertext = packed_message[ciphertext_start:ciphertext_end]
        tag = packed_message[ciphertext_end:tag_end]
        
        return {
            'salt': salt,
            'nonce': nonce,
            'ciphertext': ciphertext,
            'tag': tag
        }
    
    @staticmethod
    def calculate_packed_size(message_length: int) -> int:
        """Calculate total size after packing"""
        return GhostProtocol.HEADER_SIZE + message_length + GhostProtocol.TAG_SIZE


# Quick test
if __name__ == "__main__":
    from crypto.encryption import MessageEncryptor
    
    # Encrypt a message
    encryptor = MessageEncryptor("password123")
    encrypted = encryptor.encrypt("Test message")
    
    # Pack it
    packed = GhostProtocol.pack(encrypted)
    print(f"Packed message size: {len(packed)} bytes")
    
    # Unpack it
    unpacked = GhostProtocol.unpack(packed)
    
    # Decrypt
    decrypted = encryptor.decrypt(unpacked)
    print(f"Recovered message: {decrypted}")
    print("✅ Protocol module working correctly!")
```

---

## Step 4: Simple LSB Steganography (20 minutes)

### Create `src/steganography/lsb_stego.py`

```python
"""
LSB (Least Significant Bit) Steganography for PNG images
Simple but effective for uncompressed images
"""

from PIL import Image
import numpy as np


class LSBSteganography:
    """Hide data in image using LSB technique"""
    
    def __init__(self, image_path: str):
        """
        Initialize with cover image
        
        Args:
            image_path: Path to cover image (PNG recommended)
        """
        self.image = Image.open(image_path)
        self.image = self.image.convert('RGB')  # Ensure RGB mode
        self.width, self.height = self.image.size
    
    def calculate_capacity(self) -> int:
        """
        Calculate maximum data capacity in bytes
        
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
        Hide secret data in image
        
        Args:
            secret_data: Binary data to hide
            output_path: Where to save stego image
        """
        # Check capacity
        max_capacity = self.calculate_capacity()
        if len(secret_data) > max_capacity:
            raise ValueError(
                f"Data too large! Max capacity: {max_capacity} bytes, "
                f"Data size: {len(secret_data)} bytes"
            )
        
        # Convert image to numpy array
        img_array = np.array(self.image)
        flat_img = img_array.flatten()
        
        # Convert data to binary string
        data_len = len(secret_data)
        data_binary = ''.join(format(byte, '08b') for byte in secret_data)
        
        # Encode length in first 32 bits
        length_binary = format(data_len, '032b')
        
        # Embed length
        for i in range(32):
            flat_img[i] = (flat_img[i] & 0xFE) | int(length_binary[i])
        
        # Embed data
        for i, bit in enumerate(data_binary):
            flat_img[32 + i] = (flat_img[32 + i] & 0xFE) | int(bit)
        
        # Reshape and save
        stego_array = flat_img.reshape(img_array.shape)
        stego_image = Image.fromarray(stego_array.astype('uint8'), 'RGB')
        stego_image.save(output_path, 'PNG')
        
        print(f"✅ Hidden {data_len} bytes in {output_path}")
    
    def extract(self, stego_image_path: str) -> bytes:
        """
        Extract hidden data from stego image
        
        Args:
            stego_image_path: Path to stego image
            
        Returns:
            Extracted binary data
        """
        # Load stego image
        stego_img = Image.open(stego_image_path).convert('RGB')
        stego_array = np.array(stego_img)
        flat_img = stego_array.flatten()
        
        # Extract length (first 32 bits)
        length_binary = ''.join(str(flat_img[i] & 1) for i in range(32))
        data_len = int(length_binary, 2)
        
        # Validate length
        if data_len > self.calculate_capacity():
            raise ValueError("Invalid data length in image")
        
        # Extract data bits
        data_binary = ''.join(
            str(flat_img[32 + i] & 1) 
            for i in range(data_len * 8)
        )
        
        # Convert binary to bytes
        extracted_data = bytearray()
        for i in range(0, len(data_binary), 8):
            byte = data_binary[i:i+8]
            extracted_data.append(int(byte, 2))
        
        print(f"✅ Extracted {data_len} bytes")
        return bytes(extracted_data)


# Quick test
if __name__ == "__main__":
    # You'll need a test image - create one or use existing
    print("LSB Steganography Module")
    print("Note: Requires a test PNG image to run demo")
    print("✅ Module loaded successfully!")
```

---

## Step 5: Main Application (10 minutes)

### Create `ghost_chat.py` (in project root)

```python
"""
Ghost Chat - Steganographic Messenger
Main CLI application
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from crypto.encryption import MessageEncryptor
from protocol.ghost_protocol import GhostProtocol
from steganography.lsb_stego import LSBSteganography


def hide_message(args):
    """Hide encrypted message in image"""
    print(f"📝 Message: {args.message[:50]}...")
    print(f"🖼️  Cover image: {args.image}")
    
    # Step 1: Encrypt message
    print("\n🔒 Encrypting message...")
    encryptor = MessageEncryptor(args.password)
    encrypted = encryptor.encrypt(args.message)
    
    # Step 2: Pack into protocol format
    print("📦 Packing message...")
    packed = GhostProtocol.pack(encrypted)
    print(f"   Packed size: {len(packed)} bytes")
    
    # Step 3: Embed in image
    print("🎨 Embedding in image...")
    stego = LSBSteganography(args.image)
    
    capacity = stego.calculate_capacity()
    print(f"   Image capacity: {capacity} bytes")
    
    if len(packed) > capacity:
        print(f"❌ Error: Message too large for image!")
        print(f"   Need {len(packed)} bytes, have {capacity} bytes")
        return
    
    stego.embed(packed, args.output)
    print(f"\n✅ Success! Stego image saved to: {args.output}")
    print(f"   Original: {Path(args.image).stat().st_size} bytes")
    print(f"   Stego: {Path(args.output).stat().st_size} bytes")


def extract_message(args):
    """Extract and decrypt message from stego image"""
    print(f"🖼️  Stego image: {args.image}")
    
    # Step 1: Extract from image
    print("\n🔍 Extracting hidden data...")
    stego = LSBSteganography(args.image)
    packed = stego.extract(args.image)
    
    # Step 2: Unpack protocol message
    print("📦 Unpacking message...")
    try:
        encrypted = GhostProtocol.unpack(packed)
    except ValueError as e:
        print(f"❌ Error: {e}")
        return
    
    # Step 3: Decrypt
    print("🔓 Decrypting message...")
    encryptor = MessageEncryptor(args.password)
    try:
        message = encryptor.decrypt(encrypted)
        print(f"\n✅ Decrypted message:\n")
        print("=" * 50)
        print(message)
        print("=" * 50)
    except ValueError:
        print("❌ Decryption failed! Wrong password or corrupted data.")


def check_capacity(args):
    """Check image capacity"""
    stego = LSBSteganography(args.image)
    capacity = stego.calculate_capacity()
    print(f"🖼️  Image: {args.image}")
    print(f"📏 Dimensions: {stego.width}x{stego.height}")
    print(f"💾 Capacity: {capacity} bytes ({capacity / 1024:.2f} KB)")
    
    # Calculate typical message sizes
    print("\n📊 What you can hide:")
    print(f"   - Short message: ~200 bytes")
    print(f"   - Tweet (280 chars): ~280 bytes")
    print(f"   - Small text file: ~5 KB")
    print(f"   - This image: {capacity} bytes")


def main():
    parser = argparse.ArgumentParser(
        description='Ghost Chat - Steganographic Messenger',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Hide message in image
  python ghost_chat.py hide --image photo.png --message "Secret meeting at dawn" --password "MyPass123" --output stego.png
  
  # Extract message
  python ghost_chat.py extract --image stego.png --password "MyPass123"
  
  # Check capacity
  python ghost_chat.py capacity --image photo.png
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Hide command
    hide_parser = subparsers.add_parser('hide', help='Hide message in image')
    hide_parser.add_argument('--image', required=True, help='Cover image (PNG)')
    hide_parser.add_argument('--message', required=True, help='Message to hide')
    hide_parser.add_argument('--password', required=True, help='Encryption password')
    hide_parser.add_argument('--output', required=True, help='Output stego image')
    
    # Extract command
    extract_parser = subparsers.add_parser('extract', help='Extract message from image')
    extract_parser.add_argument('--image', required=True, help='Stego image')
    extract_parser.add_argument('--password', required=True, help='Decryption password')
    
    # Capacity command
    capacity_parser = subparsers.add_parser('capacity', help='Check image capacity')
    capacity_parser.add_argument('--image', required=True, help='Image to check')
    
    args = parser.parse_args()
    
    if args.command == 'hide':
        hide_message(args)
    elif args.command == 'extract':
        extract_message(args)
    elif args.command == 'capacity':
        check_capacity(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
```

---

## Step 6: Test It! (10 minutes)

### Create a Test Image
```python
# Create test_create_image.py
from PIL import Image
import numpy as np

# Create a simple 800x600 test image
img = Image.new('RGB', (800, 600), color=(100, 150, 200))
img.save('data/cover_images/test_cover.png')
print("✅ Created test_cover.png")
```

Run it:
```bash
python test_create_image.py
```

### Test the Full Pipeline
```bash
# Check capacity
python ghost_chat.py capacity --image data/cover_images/test_cover.png

# Hide message
python ghost_chat.py hide --image data/cover_images/test_cover.png --message "This is a secret message from Ghost Chat!" --password "SecurePass123" --output data/stego_output/stego.png

# Extract message
python ghost_chat.py extract --image data/stego_output/stego.png --password "SecurePass123"
```

---

## 🎉 Congratulations!

You now have a **working steganographic messenger**!

### What You've Built:
✅ AES-256-GCM encryption  
✅ Structured protocol format  
✅ LSB steganography  
✅ Command-line interface  

### Next Steps to Enhance:

1. **Add DCT Steganography** (for JPEG support)
2. **Implement Quality Metrics** (PSNR, SSIM)
3. **Add File-Based Input** (read message from file)
4. **Create GUI** (using tkinter or PyQt)
5. **Add Key Exchange** (ECDH for secure key sharing)

---

## 📊 Testing Checklist

- [ ] Encrypt and decrypt various message lengths
- [ ] Test with different passwords
- [ ] Test wrong password scenario
- [ ] Check capacity limits
- [ ] Compare original vs stego image visually
- [ ] Compress stego image and extract (PNG → PNG is lossless)
- [ ] Test edge cases (empty message, very long message)

---

## 🐛 Common Issues & Fixes

**Issue**: "Message too large for image"
- **Fix**: Use larger image or compress message

**Issue**: "Decryption failed"
- **Fix**: Check password is correct

**Issue**: "Invalid magic number"
- **Fix**: Ensure you're extracting from correct stego image

**Issue**: "ModuleNotFoundError"
- **Fix**: Check all files have `__init__.py` in directories

---

## 📚 File Checklist

Make sure you have:
- ✅ `ghost_chat.py` (root directory)
- ✅ `src/crypto/encryption.py`
- ✅ `src/protocol/ghost_protocol.py`
- ✅ `src/steganography/lsb_stego.py`
- ✅ `src/__init__.py`
- ✅ `src/crypto/__init__.py`
- ✅ `src/protocol/__init__.py`
- ✅ `src/steganography/__init__.py`

Create empty `__init__.py` files:
```bash
# In PowerShell
New-Item -ItemType File -Path "src\__init__.py"
New-Item -ItemType File -Path "src\crypto\__init__.py"
New-Item -ItemType File -Path "src\protocol\__init__.py"
New-Item -ItemType File -Path "src\steganography\__init__.py"
```

---

**You're ready to demo your Ghost Chat project! 🚀**
