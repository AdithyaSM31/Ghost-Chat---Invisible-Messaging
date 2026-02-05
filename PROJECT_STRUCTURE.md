# Project Ghost Chat - Suggested Directory Structure

```
Project Ghost Chat/
│
├── README.md                          # Project overview and setup instructions
├── requirements.txt                   # Python dependencies
├── setup.py                           # Installation script
│
├── ghost_chat.py                      # Main CLI entry point
│
├── src/                               # Source code
│   ├── __init__.py
│   │
│   ├── crypto/                        # Cryptography module
│   │   ├── __init__.py
│   │   ├── encryption.py              # AES-256-GCM implementation
│   │   ├── key_derivation.py          # PBKDF2/Argon2
│   │   └── key_exchange.py            # Optional: ECDH
│   │
│   ├── steganography/                 # Steganography engines
│   │   ├── __init__.py
│   │   ├── dct_stego.py               # DCT-based embedding (JPEG)
│   │   ├── lsb_stego.py               # LSB embedding (PNG)
│   │   ├── audio_stego.py             # Optional: Audio steganography
│   │   └── capacity.py                # Capacity calculation
│   │
│   ├── media/                         # Media processing
│   │   ├── __init__.py
│   │   ├── image_handler.py           # Image I/O and preprocessing
│   │   └── audio_handler.py           # Optional: Audio I/O
│   │
│   ├── protocol/                      # Message protocol
│   │   ├── __init__.py
│   │   └── ghost_protocol.py          # Message packing/unpacking
│   │
│   └── utils/                         # Utilities
│       ├── __init__.py
│       ├── metrics.py                 # PSNR, SSIM calculations
│       ├── validators.py              # Input validation
│       └── logger.py                  # Logging configuration
│
├── tests/                             # Unit tests
│   ├── __init__.py
│   ├── test_encryption.py
│   ├── test_dct_stego.py
│   ├── test_lsb_stego.py
│   ├── test_protocol.py
│   └── test_integration.py
│
├── examples/                          # Example scripts
│   ├── basic_usage.py
│   ├── batch_processing.py
│   └── key_exchange_demo.py
│
├── data/                              # Test data
│   ├── cover_images/                  # Sample cover images
│   ├── test_messages/                 # Test messages
│   └── stego_output/                  # Generated stego images
│
├── docs/                              # Documentation
│   ├── technical_report.md
│   ├── user_manual.md
│   ├── security_analysis.md
│   └── api_reference.md
│
└── notebooks/                         # Jupyter notebooks (optional)
    ├── dct_analysis.ipynb             # Visualize DCT coefficients
    └── quality_metrics.ipynb          # Analyze embedding quality
```

## File Descriptions

### Core Implementation Files

**`ghost_chat.py`** - Main CLI application:
```python
import argparse
from src.crypto.encryption import MessageEncryptor
from src.steganography.dct_stego import DCTSteganography
from src.protocol.ghost_protocol import GhostProtocol

def main():
    parser = argparse.ArgumentParser(description='Project Ghost Chat')
    subparsers = parser.add_subparsers(dest='command')
    
    # Hide command
    hide_parser = subparsers.add_parser('hide')
    hide_parser.add_argument('--image', required=True)
    hide_parser.add_argument('--message', required=True)
    hide_parser.add_argument('--password', required=True)
    hide_parser.add_argument('--output', required=True)
    
    # Extract command
    extract_parser = subparsers.add_parser('extract')
    extract_parser.add_argument('--image', required=True)
    extract_parser.add_argument('--password', required=True)
    
    args = parser.parse_args()
    # Implementation...
```

**`requirements.txt`**:
```
pycryptodome>=3.19.0
Pillow>=10.0.0
numpy>=1.24.0
scipy>=1.11.0
opencv-python>=4.8.0
scikit-image>=0.21.0
argparse>=1.4.0
colorama>=0.4.6
tqdm>=4.66.0
```

### Module Responsibilities

| Module | Responsibility |
|--------|---------------|
| `crypto/encryption.py` | AES-256-GCM encryption/decryption |
| `crypto/key_derivation.py` | PBKDF2, Argon2 implementations |
| `steganography/dct_stego.py` | DCT-based embedding/extraction |
| `steganography/lsb_stego.py` | LSB-based embedding/extraction |
| `protocol/ghost_protocol.py` | Message format packing |
| `media/image_handler.py` | Image loading, conversion, validation |
| `utils/metrics.py` | PSNR, SSIM, capacity calculations |

## Development Workflow

### 1. **Initial Setup**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/
```

### 2. **Development Order**
1. Start with `crypto/encryption.py`
2. Implement `protocol/ghost_protocol.py`
3. Build `steganography/lsb_stego.py` (simpler)
4. Advance to `steganography/dct_stego.py` (complex)
5. Create `ghost_chat.py` CLI
6. Add tests and documentation

### 3. **Testing Strategy**
```bash
# Unit tests
pytest tests/test_encryption.py

# Integration tests
pytest tests/test_integration.py

# Coverage report
pytest --cov=src tests/
```

## Quick Start Template

Create these files first to get started:

### 1. `requirements.txt`
See above

### 2. `src/crypto/encryption.py` (Basic Template)
```python
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Random import get_random_bytes

class MessageEncryptor:
    def __init__(self, password: str, salt: bytes = None):
        self.salt = salt or get_random_bytes(32)
        self.key = PBKDF2(password, self.salt, dkLen=32, count=100000)
    
    def encrypt(self, plaintext: str) -> tuple:
        cipher = AES.new(self.key, AES.MODE_GCM)
        ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode('utf-8'))
        return self.salt, cipher.nonce, ciphertext, tag
    
    def decrypt(self, salt: bytes, nonce: bytes, ciphertext: bytes, tag: bytes) -> str:
        self.salt = salt
        self.key = PBKDF2(self.key, salt, dkLen=32, count=100000)
        cipher = AES.new(self.key, AES.MODE_GCM, nonce=nonce)
        plaintext = cipher.decrypt_and_verify(ciphertext, tag)
        return plaintext.decode('utf-8')
```

### 3. `tests/test_encryption.py`
```python
import pytest
from src.crypto.encryption import MessageEncryptor

def test_encrypt_decrypt():
    password = "TestPassword123"
    message = "Secret message"
    
    encryptor = MessageEncryptor(password)
    salt, nonce, ciphertext, tag = encryptor.encrypt(message)
    
    decryptor = MessageEncryptor(password, salt)
    decrypted = decryptor.decrypt(salt, nonce, ciphertext, tag)
    
    assert decrypted == message

def test_wrong_password():
    password = "CorrectPassword"
    wrong_password = "WrongPassword"
    message = "Secret"
    
    encryptor = MessageEncryptor(password)
    salt, nonce, ciphertext, tag = encryptor.encrypt(message)
    
    decryptor = MessageEncryptor(wrong_password, salt)
    with pytest.raises(ValueError):
        decryptor.decrypt(salt, nonce, ciphertext, tag)
```

## Git Setup (Optional)

```bash
# Initialize repository
git init

# Create .gitignore
echo "venv/" >> .gitignore
echo "__pycache__/" >> .gitignore
echo "*.pyc" >> .gitignore
echo ".pytest_cache/" >> .gitignore
echo "data/stego_output/" >> .gitignore
echo ".env" >> .gitignore

# First commit
git add .
git commit -m "Initial project structure"
```

---

This structure provides modularity, testability, and scalability for your Ghost Chat project!
