"""
Example: Basic usage of Ghost Chat
Demonstrates hiding and extracting messages
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from crypto.encryption import MessageEncryptor
from protocol.ghost_protocol import GhostProtocol
from steganography.lsb_stego import LSBSteganography


def basic_example():
    """Basic example of hiding and extracting a message"""
    print("=" * 60)
    print("Ghost Chat - Basic Usage Example")
    print("=" * 60)
    
    # Configuration
    PASSWORD = "MySecurePassword123!"
    MESSAGE = "This is a secret message that will be hidden in an image!"
    COVER_IMAGE = "data/cover_images/solid_small.png"
    STEGO_IMAGE = "data/stego_output/example_stego.png"
    
    print(f"\n📝 Message: {MESSAGE}")
    print(f"🔑 Password: {PASSWORD}")
    print(f"🖼️  Cover: {COVER_IMAGE}")
    
    # Step 1: Encryption
    print("\n" + "-" * 60)
    print("Step 1: Encrypting message...")
    encryptor = MessageEncryptor(PASSWORD)
    encrypted = encryptor.encrypt(MESSAGE)
    print(f"✅ Encrypted: {len(encrypted['ciphertext'])} bytes")
    
    # Step 2: Protocol Packing
    print("\n" + "-" * 60)
    print("Step 2: Packing into protocol format...")
    packed = GhostProtocol.pack(encrypted)
    print(f"✅ Packed: {len(packed)} bytes")
    
    # Step 3: Steganography
    print("\n" + "-" * 60)
    print("Step 3: Hiding in image...")
    stego = LSBSteganography(COVER_IMAGE)
    capacity = stego.calculate_capacity()
    print(f"   Image capacity: {capacity:,} bytes")
    
    if len(packed) > capacity:
        print("❌ Message too large!")
        return
    
    stego.embed(packed, STEGO_IMAGE)
    print(f"✅ Stego image created: {STEGO_IMAGE}")
    
    # Extraction
    print("\n" + "=" * 60)
    print("EXTRACTION")
    print("=" * 60)
    
    # Step 4: Extract from image
    print("\nStep 1: Extracting from image...")
    extracted_packed = stego.extract(STEGO_IMAGE)
    print(f"✅ Extracted: {len(extracted_packed)} bytes")
    
    # Step 5: Unpack protocol
    print("\nStep 2: Unpacking protocol...")
    extracted_encrypted = GhostProtocol.unpack(extracted_packed)
    print(f"✅ Unpacked successfully")
    
    # Step 6: Decrypt
    print("\nStep 3: Decrypting...")
    decrypted = encryptor.decrypt(extracted_encrypted)
    print(f"✅ Decrypted message:")
    print(f"\n   \"{decrypted}\"")
    
    # Verify
    print("\n" + "=" * 60)
    if decrypted == MESSAGE:
        print("✅ SUCCESS! Message recovered correctly!")
    else:
        print("❌ FAILURE! Message mismatch!")
    print("=" * 60)


if __name__ == "__main__":
    # Check if test image exists
    cover_path = Path("data/cover_images/solid_small.png")
    if not cover_path.exists():
        print("⚠️  Test image not found. Creating it...")
        from create_test_image import create_solid_color_image
        cover_path.parent.mkdir(parents=True, exist_ok=True)
        create_solid_color_image(800, 600, str(cover_path))
    
    # Ensure output directory exists
    Path("data/stego_output").mkdir(parents=True, exist_ok=True)
    
    # Run example
    basic_example()
