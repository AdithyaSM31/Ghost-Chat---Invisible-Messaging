"""
Ghost Chat message protocol for structured payload
Handles message packing and unpacking with header structure
"""

import struct


class GhostProtocol:
    """Handles message packing and unpacking"""
    
    # Protocol constants
    MAGIC = b'GHST'  # Magic number to identify Ghost messages
    VERSION = 1       # Protocol version
    HEADER_SIZE = 68  # Fixed header size (updated for 16-byte nonce)
    TAG_SIZE = 16     # GCM authentication tag size
    NONCE_SIZE = 16   # AES-GCM nonce size
    
    @staticmethod
    def pack(encrypted_data: dict) -> bytes:
        """
        Pack encrypted data into protocol format
        
        Message Format:
        ┌──────────────────────────────────────────────────────┐
        │ HEADER (68 bytes)                                     │
        ├──────────────────────────────────────────────────────┤
        │ - Magic Number (4 bytes): "GHST"                      │
        │ - Protocol Version (2 bytes): 0x0001                  │
        │ - Payload Length (4 bytes): Size of encrypted data   │
        │ - Salt (32 bytes): For key derivation                │
        │ - Nonce (16 bytes): For AES-GCM                       │
        │ - Reserved (10 bytes): Future use                     │
        ├──────────────────────────────────────────────────────┤
        │ ENCRYPTED PAYLOAD (variable)                          │
        ├──────────────────────────────────────────────────────┤
        │ - Ciphertext (variable length)                        │
        │ - Authentication Tag (16 bytes): GCM tag              │
        └──────────────────────────────────────────────────────┘
        
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
        
        # Validate sizes
        if len(salt) != 32:
            raise ValueError(f"Salt must be 32 bytes, got {len(salt)}")
        if len(nonce) != GhostProtocol.NONCE_SIZE:
            raise ValueError(f"Nonce must be {GhostProtocol.NONCE_SIZE} bytes, got {len(nonce)}")
        if len(tag) != 16:
            raise ValueError(f"Tag must be 16 bytes, got {len(tag)}")
        
        # Build header using network byte order (big-endian)
        header = struct.pack(
            '!4sHI32s16s10s',
            GhostProtocol.MAGIC,           # Magic number (4 bytes)
            GhostProtocol.VERSION,         # Version (2 bytes)
            len(ciphertext),                # Payload length (4 bytes)
            salt,                           # Salt (32 bytes)
            nonce,                          # Nonce (16 bytes)
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
            
        Raises:
            ValueError: If message is invalid or corrupted
        """
        # Validate minimum length
        min_size = GhostProtocol.HEADER_SIZE + GhostProtocol.TAG_SIZE
        if len(packed_message) < min_size:
            raise ValueError(
                f"Message too short to be valid Ghost protocol "
                f"(got {len(packed_message)} bytes, need at least {min_size})"
            )
        
        # Unpack header
        header_data = struct.unpack(
            '!4sHI32s16s10s',
            packed_message[:GhostProtocol.HEADER_SIZE]
        )
        
        magic, version, payload_len, salt, nonce, _ = header_data
        
        # Validate magic number
        if magic != GhostProtocol.MAGIC:
            raise ValueError(
                f"Invalid magic number: expected {GhostProtocol.MAGIC}, "
                f"got {magic}. This may not be a Ghost Chat message."
            )
        
        # Validate version
        if version != GhostProtocol.VERSION:
            raise ValueError(
                f"Unsupported protocol version: {version}. "
                f"This implementation supports version {GhostProtocol.VERSION}."
            )
        
        # Validate payload length
        expected_total_size = GhostProtocol.HEADER_SIZE + payload_len + GhostProtocol.TAG_SIZE
        if len(packed_message) < expected_total_size:
            raise ValueError(
                f"Message truncated: expected {expected_total_size} bytes, "
                f"got {len(packed_message)} bytes"
            )
        
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
        """
        Calculate total size after packing
        
        Args:
            message_length: Length of plaintext message in bytes
            
        Returns:
            Total packed size in bytes
        """
        return GhostProtocol.HEADER_SIZE + message_length + GhostProtocol.TAG_SIZE


# Self-test function
def _test():
    """Test the protocol module"""
    print("Testing GhostProtocol...")
    
    # Import here to avoid circular dependency
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from crypto.encryption import MessageEncryptor
    
    # Encrypt a message
    encryptor = MessageEncryptor("password123")
    message = "Test message for protocol validation"
    encrypted = encryptor.encrypt(message)
    
    print(f"Original message: {message}")
    print(f"Encrypted size: {len(encrypted['ciphertext'])} bytes")
    
    # Pack it
    packed = GhostProtocol.pack(encrypted)
    print(f"Packed message size: {len(packed)} bytes")
    print(f"Magic number: {packed[:4]}")
    
    # Calculate expected size
    expected_size = GhostProtocol.calculate_packed_size(len(encrypted['ciphertext']))
    print(f"Expected size: {expected_size} bytes")
    assert len(packed) == expected_size, "Size mismatch!"
    
    # Unpack it
    unpacked = GhostProtocol.unpack(packed)
    print(f"Unpacked ciphertext size: {len(unpacked['ciphertext'])} bytes")
    
    # Decrypt
    decrypted = encryptor.decrypt(unpacked)
    print(f"Recovered message: {decrypted}")
    
    assert message == decrypted, "Message mismatch!"
    print("✅ Protocol module working correctly!")
    
    # Test invalid message
    print("\nTesting invalid message detection...")
    try:
        GhostProtocol.unpack(b"INVALID" + b"\x00" * 100)
        print("❌ Error: Should have rejected invalid message!")
    except ValueError as e:
        print(f"✅ Correctly rejected invalid message: {e}")


if __name__ == "__main__":
    _test()
