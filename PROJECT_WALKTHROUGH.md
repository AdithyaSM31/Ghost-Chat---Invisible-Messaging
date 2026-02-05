# Steganographic Ghost Messenger - Project Walkthrough
## (Project Ghost Chat)

---

## 📋 Project Overview

**Goal**: Create a secure messaging system that hides AES-256 encrypted messages within digital media (images/audio) using DCT-based steganography to achieve deniable authenticity and avoid metadata profiling.

**Key Concept**: Even if someone detects encrypted traffic, the steganographic approach makes the communication look like innocent media sharing, preventing adversaries from knowing:
- Who is communicating
- When the communication occurred  
- What pattern of communication exists

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    USER INTERFACE                        │
│         (Message Input/Output, Media Selection)          │
└───────────────────┬─────────────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────────────┐
│              ENCRYPTION LAYER                            │
│   • AES-256-GCM (Authenticated Encryption)               │
│   • Key Derivation (PBKDF2/Argon2)                       │
│   • Optional: Public Key Exchange (ECDH)                 │
└───────────────────┬─────────────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────────────┐
│           STEGANOGRAPHY ENGINE                           │
│   • DCT-based embedding for JPEG images                  │
│   • LSB/Phase coding for audio (WAV/MP3)                 │
│   • Capacity calculation & optimization                  │
└───────────────────┬─────────────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────────────┐
│              MEDIA HANDLER                               │
│   • Image processing (PIL/OpenCV)                        │
│   • Audio processing (librosa/pydub)                     │
│   • Format conversion & validation                       │
└───────────────────┬─────────────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────────────┐
│         TRANSMISSION LAYER (Optional)                    │
│   • Socket-based P2P communication                       │
│   • File sharing via standard channels                   │
└─────────────────────────────────────────────────────────┘
```

---

## 🔧 Core Components Breakdown

### 1. **Encryption Module** (`encryption.py`)

**Purpose**: Encrypt messages before embedding them into media

**Key Features**:
- **AES-256-GCM**: Provides both confidentiality and authenticity
- **Key Derivation**: PBKDF2 or Argon2 for password-based keys
- **Salt & Nonce**: Random values to prevent rainbow table attacks
- **HMAC**: Message authentication to detect tampering

**Implementation Steps**:
```python
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Random import get_random_bytes
import hashlib

class MessageEncryptor:
    def __init__(self, password):
        # Derive key from password
        self.salt = get_random_bytes(32)
        self.key = PBKDF2(password, self.salt, dkLen=32, count=100000)
    
    def encrypt(self, plaintext):
        # Use AES-GCM for authenticated encryption
        cipher = AES.new(self.key, AES.MODE_GCM)
        ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode())
        return cipher.nonce, ciphertext, tag
    
    def decrypt(self, nonce, ciphertext, tag):
        cipher = AES.new(self.key, AES.MODE_GCM, nonce=nonce)
        plaintext = cipher.decrypt_and_verify(ciphertext, tag)
        return plaintext.decode()
```

---

### 2. **DCT Steganography Module** (`dct_stego.py`)

**Purpose**: Hide encrypted data in JPEG images using DCT coefficients

**Why DCT?**
- JPEG compression uses DCT → modifying DCT coefficients is less detectable
- Robust against compression
- Can survive JPEG re-encoding

**DCT-Based Embedding Algorithm**:

1. **Divide image into 8x8 blocks**
2. **Apply DCT to each block**
3. **Select mid-frequency coefficients** (avoid low-freq for robustness, avoid high-freq that get lost in compression)
4. **Embed bits by modifying LSBs of DCT coefficients**
5. **Apply inverse DCT**

**Implementation Approach**:
```python
import numpy as np
from scipy.fftpack import dct, idct
from PIL import Image

class DCTSteganography:
    def __init__(self, image_path):
        self.img = Image.open(image_path).convert('RGB')
        self.img_array = np.array(self.img)
    
    def embed_message(self, encrypted_data):
        """
        Embed encrypted message into DCT coefficients
        """
        # Convert encrypted data to binary
        binary_data = ''.join(format(byte, '08b') for byte in encrypted_data)
        
        # Get image dimensions
        height, width, channels = self.img_array.shape
        
        # Process Y channel (luminance) in YCbCr color space
        ycbcr_img = self.img.convert('YCbCr')
        y_channel = np.array(ycbcr_img)[:,:,0].astype(float)
        
        # Embed in 8x8 blocks
        data_index = 0
        for i in range(0, height-8, 8):
            for j in range(0, width-8, 8):
                if data_index >= len(binary_data):
                    break
                    
                block = y_channel[i:i+8, j:j+8]
                dct_block = dct(dct(block.T, norm='ortho').T, norm='ortho')
                
                # Embed in mid-frequency coefficient (e.g., position [3,4])
                if binary_data[data_index] == '1':
                    dct_block[3, 4] = abs(dct_block[3, 4]) | 1
                else:
                    dct_block[3, 4] = abs(dct_block[3, 4]) & ~1
                
                # Inverse DCT
                idct_block = idct(idct(dct_block.T, norm='ortho').T, norm='ortho')
                y_channel[i:i+8, j:j+8] = idct_block
                data_index += 1
        
        # Reconstruct image
        return self._reconstruct_image(y_channel, ycbcr_img)
    
    def extract_message(self, message_length):
        """
        Extract hidden message from DCT coefficients
        """
        ycbcr_img = self.img.convert('YCbCr')
        y_channel = np.array(ycbcr_img)[:,:,0].astype(float)
        
        binary_data = ""
        height, width = y_channel.shape
        
        for i in range(0, height-8, 8):
            for j in range(0, width-8, 8):
                if len(binary_data) >= message_length * 8:
                    break
                    
                block = y_channel[i:i+8, j:j+8]
                dct_block = dct(dct(block.T, norm='ortho').T, norm='ortho')
                
                # Extract bit from coefficient
                bit = int(abs(dct_block[3, 4])) & 1
                binary_data += str(bit)
        
        # Convert binary to bytes
        message_bytes = bytearray()
        for i in range(0, len(binary_data), 8):
            byte = binary_data[i:i+8]
            message_bytes.append(int(byte, 2))
        
        return bytes(message_bytes)
```

**Key DCT Embedding Positions**:
- **Low frequency (top-left)**: Contains most visual information → avoid
- **Mid frequency**: Good balance of robustness and invisibility → **USE THIS**
- **High frequency (bottom-right)**: Lost during compression → avoid

---

### 3. **LSB Steganography Module** (`lsb_stego.py`)

**Purpose**: Alternative/complementary method for PNG images or audio

**Algorithm**:
1. Convert message to binary
2. Replace least significant bits of pixel values/audio samples
3. Changes are imperceptible to human eye/ear

**Implementation**:
```python
class LSBSteganography:
    def embed(self, cover_image, secret_data):
        img = Image.open(cover_image).convert('RGB')
        pixels = np.array(img)
        
        # Flatten and convert data to binary
        binary_data = ''.join(format(byte, '08b') for byte in secret_data)
        data_len = len(binary_data)
        
        flat_pixels = pixels.flatten()
        
        # Embed length first (32 bits)
        length_binary = format(data_len, '032b')
        for i in range(32):
            flat_pixels[i] = (flat_pixels[i] & ~1) | int(length_binary[i])
        
        # Embed data
        for i in range(data_len):
            flat_pixels[32 + i] = (flat_pixels[32 + i] & ~1) | int(binary_data[i])
        
        stego_pixels = flat_pixels.reshape(pixels.shape)
        return Image.fromarray(stego_pixels.astype('uint8'), 'RGB')
    
    def extract(self, stego_image):
        img = Image.open(stego_image).convert('RGB')
        pixels = np.array(img).flatten()
        
        # Extract length
        length_binary = ''.join(str(pixels[i] & 1) for i in range(32))
        data_len = int(length_binary, 2)
        
        # Extract data
        binary_data = ''.join(str(pixels[32 + i] & 1) for i in range(data_len))
        
        # Convert to bytes
        secret_data = bytearray()
        for i in range(0, len(binary_data), 8):
            byte = binary_data[i:i+8]
            secret_data.append(int(byte, 2))
        
        return bytes(secret_data)
```

---

### 4. **Message Format** (`protocol.py`)

**Purpose**: Structure the hidden payload for reliable extraction

**Recommended Format**:
```
┌──────────────────────────────────────────────────────┐
│ HEADER (64 bytes)                                     │
├──────────────────────────────────────────────────────┤
│ - Magic Number (4 bytes): "GHST"                      │
│ - Protocol Version (2 bytes): 0x0001                  │
│ - Payload Length (4 bytes): Size of encrypted data   │
│ - Salt (32 bytes): For key derivation                │
│ - Nonce (12 bytes): For AES-GCM                       │
│ - Reserved (10 bytes): Future use                     │
├──────────────────────────────────────────────────────┤
│ ENCRYPTED PAYLOAD (variable)                          │
├──────────────────────────────────────────────────────┤
│ - Ciphertext (variable length)                        │
│ - Authentication Tag (16 bytes): GCM tag              │
└──────────────────────────────────────────────────────┘
```

**Implementation**:
```python
import struct

class GhostProtocol:
    MAGIC = b'GHST'
    VERSION = 0x0001
    
    @staticmethod
    def pack_message(salt, nonce, ciphertext, tag):
        header = struct.pack(
            '!4sHI32s12s10s',
            GhostProtocol.MAGIC,
            GhostProtocol.VERSION,
            len(ciphertext),
            salt,
            nonce,
            b'\x00' * 10  # Reserved
        )
        return header + ciphertext + tag
    
    @staticmethod
    def unpack_message(data):
        if len(data) < 64:
            raise ValueError("Invalid message: too short")
        
        magic, version, payload_len, salt, nonce, _ = struct.unpack(
            '!4sHI32s12s10s',
            data[:64]
        )
        
        if magic != GhostProtocol.MAGIC:
            raise ValueError("Invalid magic number")
        
        ciphertext = data[64:64+payload_len]
        tag = data[64+payload_len:64+payload_len+16]
        
        return salt, nonce, ciphertext, tag
```

---

## 🚀 Implementation Roadmap

### **Phase 1: Core Encryption (Week 1)**
- [ ] Implement AES-256-GCM encryption/decryption
- [ ] Add PBKDF2 key derivation
- [ ] Test with various message sizes
- [ ] Implement protocol message packing

### **Phase 2: Image Steganography (Week 2)**
- [ ] Implement DCT-based embedding for JPEG
- [ ] Implement LSB embedding for PNG
- [ ] Calculate embedding capacity
- [ ] Test imperceptibility (PSNR, SSIM metrics)

### **Phase 3: Audio Steganography (Week 3)** _(Optional)_
- [ ] Implement phase coding for audio
- [ ] Test with WAV files
- [ ] Ensure audio quality preservation

### **Phase 4: Integration & UI (Week 4)**
- [ ] Create command-line interface
- [ ] Add file selection and validation
- [ ] Integrate encryption + steganography pipeline
- [ ] Add error handling

### **Phase 5: Testing & Validation (Week 5)**
- [ ] Security analysis
- [ ] Steganalysis resistance testing
- [ ] Performance benchmarking
- [ ] Documentation

---

## 🛠️ Technology Stack

### **Programming Language**: Python 3.8+

### **Required Libraries**:
```bash
# Cryptography
pip install pycryptodome

# Image Processing
pip install Pillow numpy scipy opencv-python

# Audio Processing (Optional)
pip install librosa pydub wave

# Utilities
pip install argparse colorama tqdm
```

---

## 📊 Security Considerations

### **Cryptographic Security**:
1. ✅ **Use AES-256-GCM** (provides authenticated encryption)
2. ✅ **Random salts and nonces** for each message
3. ✅ **Strong key derivation** (PBKDF2 with 100k+ iterations or Argon2)
4. ⚠️ **Secure key exchange**: Consider ECDH for key agreement

### **Steganographic Security**:
1. ✅ **DCT-based embedding** is robust against JPEG recompression
2. ⚠️ **Avoid LSB in JPEG** (lost during compression)
3. ✅ **Limit embedding rate** to <10% of coefficients to avoid detection
4. ⚠️ **Chi-square attack resistance**: Randomize embedding positions

### **Operational Security**:
1. ✅ **Use innocent-looking cover images** (vacation photos, memes)
2. ✅ **Vary cover media** to avoid pattern recognition
3. ⚠️ **Avoid metadata**: Strip EXIF data before sharing
4. ✅ **Deniability**: Encrypted payload looks like random noise if detected

---

## 🧪 Testing & Validation

### **1. Visual Quality Metrics**

**PSNR (Peak Signal-to-Noise Ratio)**:
```python
def calculate_psnr(original, stego):
    mse = np.mean((original - stego) ** 2)
    if mse == 0:
        return float('inf')
    max_pixel = 255.0
    psnr = 20 * np.log10(max_pixel / np.sqrt(mse))
    return psnr

# Target: PSNR > 40 dB (imperceptible)
```

**SSIM (Structural Similarity Index)**:
```python
from skimage.metrics import structural_similarity as ssim

def calculate_ssim(original, stego):
    return ssim(original, stego, multichannel=True)

# Target: SSIM > 0.95 (high similarity)
```

### **2. Capacity Testing**
```python
def calculate_capacity(image_path, method='DCT'):
    img = Image.open(image_path)
    width, height = img.size
    
    if method == 'DCT':
        # One bit per 8x8 block (conservative estimate)
        capacity_bits = (width // 8) * (height // 8)
    elif method == 'LSB':
        # Three bits per pixel (R, G, B channels)
        capacity_bits = width * height * 3
    
    capacity_bytes = capacity_bits // 8
    return capacity_bytes

# Example: 1920x1080 image with DCT = ~30KB capacity
```

### **3. Steganalysis Resistance**

Test against common attacks:
- **Chi-square test**: Detects LSB embedding patterns
- **RS Analysis**: Detects sequential LSB embedding
- **Histogram analysis**: Detects unusual bit distributions

**Mitigation**: Use DCT, randomize embedding positions, limit embedding rate

---

## 💻 Command-Line Interface Design

```bash
# Encrypt and hide message
python ghost_chat.py hide \
    --image cover.jpg \
    --message "Secret meeting at dawn" \
    --password "MySecurePass123!" \
    --output stego.jpg

# Extract and decrypt message
python ghost_chat.py extract \
    --image stego.jpg \
    --password "MySecurePass123!" \
    --output message.txt

# Capacity check
python ghost_chat.py capacity --image cover.jpg

# Generate key pair for public key mode
python ghost_chat.py keygen --output keypair.pem
```

---

## 🎯 Key Deliverables

1. **Source Code**:
   - Modular Python implementation
   - Well-documented functions
   - Unit tests

2. **Documentation**:
   - Technical report explaining algorithms
   - User manual with examples
   - Security analysis

3. **Demo**:
   - Working prototype
   - Before/after image comparison
   - Performance metrics

4. **Presentation**:
   - Problem statement
   - Technical approach
   - Security evaluation
   - Future enhancements

---

## 🔮 Advanced Features (Optional)

### **1. Public Key Cryptography**
Use ECDH (Elliptic Curve Diffie-Hellman) for key exchange:
```python
from Crypto.PublicKey import ECC
from Crypto.Protocol.KDF import HKDF
from Crypto.Hash import SHA256

# Sender generates ephemeral key pair
sender_key = ECC.generate(curve='P-256')

# ECDH shared secret with recipient's public key
shared_secret = sender_key.d * recipient_public_key.pointQ

# Derive AES key
aes_key = HKDF(shared_secret.x, 32, b'', SHA256)
```

### **2. Multi-Layer Steganography**
- Embed encrypted message in image
- Embed that image in audio file
- Increase deniability

### **3. Blockchain Timestamping**
- Hash stego media and store on blockchain
- Provides non-repudiation without revealing content

### **4. Stealth Channels**
- Upload to social media (Facebook, Instagram)
- Use cover traffic (photos already being shared)

---

## 📚 References & Resources

### **Academic Papers**:
1. Cox et al., "Secure Spread Spectrum Watermarking" (1997)
2. Provos & Honeyman, "Hide and Seek: An Introduction to Steganography" (2001)
3. Fridrich, "Steganography in Digital Media" (2009)

### **Tools for Analysis**:
- **StegExpose**: Machine learning-based steganalysis
- **OpenPuff**: Multi-carrier steganography tool
- **Stegdetect**: JPEG steganography detector

### **Cryptographic Best Practices**:
- NIST Guidelines for Key Management
- OWASP Cryptographic Storage Cheat Sheet

---

## ⚖️ Ethical & Legal Notice

**Important**: This tool is for educational purposes and legitimate privacy protection. Users are responsible for complying with local laws regarding:
- Encryption export controls
- Steganography usage
- Data protection regulations

**Responsible Use**: Always obtain consent before hiding data in media you don't own.

---

## 🎓 Learning Outcomes

By completing this project, you will:
- ✅ Understand symmetric encryption (AES-256-GCM)
- ✅ Master digital signal processing (DCT, frequency domain)
- ✅ Learn steganography techniques and limitations
- ✅ Implement security protocols
- ✅ Analyze cryptographic systems
- ✅ Develop secure coding practices

---

## 📝 Project Tips

1. **Start Simple**: Get basic LSB working before tackling DCT
2. **Test Incrementally**: Verify each module independently
3. **Visualize**: Plot DCT coefficients to understand embedding
4. **Measure Quality**: Always check PSNR/SSIM after embedding
5. **Document Everything**: Future you will thank present you
6. **Security First**: Never roll your own crypto primitives

---

## 🚨 Common Pitfalls to Avoid

1. ❌ **Don't use ECB mode** → Use GCM or CBC with HMAC
2. ❌ **Don't reuse nonces** → Generate fresh random nonces
3. ❌ **Don't embed too much** → Keep rate <10% for stealth
4. ❌ **Don't ignore JPEG compression** → Use DCT, not LSB
5. ❌ **Don't hardcode keys** → Derive from user passwords
6. ❌ **Don't forget authentication** → Use GCM or add HMAC

---

**Good luck with your project! 🚀**

Remember: "Security through obscurity" alone is weak. Combine strong encryption with steganography for defense in depth!
