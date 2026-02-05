"""
AES-256-GCM encryption module for Ghost Chat
Provides secure message encryption and decryption
"""

from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Random import get_random_bytes


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
        # Using 100,000 iterations for strong key derivation
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
            
        Raises:
            ValueError: If decryption fails (wrong password or corrupted data)
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


# Self-test function
def _test():
    """Test the encryption module"""
    print("Testing MessageEncryptor...")
    
    encryptor = MessageEncryptor("MySecurePassword123!")
    
    message = "This is a secret message!"
    print(f"Original: {message}")
    
    # Encrypt
    encrypted = encryptor.encrypt(message)
    print(f"Encrypted: {encrypted['ciphertext'][:20]}... (showing first 20 bytes)")
    print(f"Salt: {encrypted['salt'][:16].hex()}...")
    print(f"Nonce: {encrypted['nonce'].hex()}")
    
    # Decrypt
    decrypted = encryptor.decrypt(encrypted)
    print(f"Decrypted: {decrypted}")
    
    assert message == decrypted, "Encryption/Decryption failed!"
    print("✅ Encryption module working correctly!")
    
    # Test wrong password
    print("\nTesting wrong password...")
    wrong_encryptor = MessageEncryptor("WrongPassword")
    try:
        wrong_encryptor.decrypt(encrypted)
        print("❌ Error: Should have failed with wrong password!")
    except ValueError as e:
        print(f"✅ Correctly rejected wrong password: {e}")


if __name__ == "__main__":
    _test()
