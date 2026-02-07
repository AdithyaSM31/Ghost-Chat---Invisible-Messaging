# Ghost Chat - Steganographic Messenger

<div align="center">
  <img src="logo.png" alt="Ghost Chat Logo" width="150" height="auto" />
  <br>
  <em>Secrets in the Pixel World</em>
</div>

<br>

A secure messaging tool that hides AES-256 encrypted messages within images using steganography, achieving deniable authenticity and avoiding metadata profiling. Now available as a **Web App** and **Offline Android App**.

## 📱 Mobile App (Android)

Access hidden communications on the go with the new hybrid Android app.

- **100% Offline Encryption**: All processing happens on your device using `ghost-engine.js`.
- **Native File Saving**: Directly saves generated stego-images to your Documents/Pictures folder.
- **Stealth UI**: Glassmorphism design inspired by cyber-sec aesthetics.

### Building for Android
1. **Install Node.js & Dependencies**
   ```bash
   npm install
   ```
2. **Sync with Android Project**
   ```bash
   npx cap sync android
   ```
3. **Open in Android Studio**
   ```bash
   npx cap open android
   ```

---

## 🎯 Project Overview

**Purpose**: Create undetectable communication by hiding encrypted messages in innocent-looking images, preventing surveillance entities from identifying communication patterns.

**Key Features**:
- 🔒 AES-256-GCM encryption (authenticated encryption)
- 🖼️ LSB steganography for PNG images
- 📦 Structured protocol format
- 🛡️ Deniable authenticity
- 🚫 Metadata protection

## 🚀 Quick Start

### Installation

1. **Clone or download the project**

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

### Usage

#### Hide a Message
```bash
python ghost_chat.py hide \
    --image photo.png \
    --message "Secret meeting at dawn" \
    --password "MySecurePassword123!" \
    --output stego.png
```

#### Extract a Message
```bash
python ghost_chat.py extract \
    --image stego.png \
    --password "MySecurePassword123!"
```

#### Check Image Capacity
```bash
python ghost_chat.py capacity --image photo.png
```

## 📁 Project Structure

```
Project Ghost Chat/
├── ghost_chat.py              # Main CLI application
├── requirements.txt           # Python dependencies
├── README.md                  # This file
├── src/                       # Source code
│   ├── crypto/               # Cryptography module
│   │   └── encryption.py     # AES-256-GCM encryption
│   ├── protocol/             # Message protocol
│   │   └── ghost_protocol.py # Message packing/unpacking
│   └── steganography/        # Steganography engines
│       └── lsb_stego.py      # LSB steganography
├── data/                      # Test data
│   ├── cover_images/         # Original images
│   └── stego_output/         # Generated stego images
├── tests/                     # Unit tests
└── examples/                  # Example scripts
```

## 🔧 How It Works

### 1. Encryption Layer
- Uses **AES-256-GCM** for authenticated encryption
- **PBKDF2** key derivation from password (100,000 iterations)
- Random salt and nonce for each message
- Provides confidentiality and authenticity

### 2. Protocol Layer
- Structured message format with header
- Magic number for message identification
- Includes salt, nonce, ciphertext, and authentication tag
- Total overhead: 80 bytes (64-byte header + 16-byte tag)

### 3. Steganography Layer
- **LSB (Least Significant Bit)** technique for PNG images
- Modifies the least significant bit of RGB pixel values
- Imperceptible to human eye
- First 32 bits encode message length

### Message Flow
```
Plaintext → Encrypt → Pack Protocol → Embed in Image → Stego Image
Stego Image → Extract → Unpack Protocol → Decrypt → Plaintext
```

## 🧪 Testing

### Test Individual Modules
```bash
# Test encryption
python src/crypto/encryption.py

# Test protocol
python src/protocol/ghost_protocol.py

# Test steganography
python src/steganography/lsb_stego.py
```

### Create Test Image
```bash
python examples/create_test_image.py
```

## 🔒 Security Features

1. **Encryption**: AES-256-GCM with authenticated encryption
2. **Key Derivation**: PBKDF2 with 100,000 iterations
3. **Random Salt**: Unique for each message
4. **Random Nonce**: Prevents replay attacks
5. **Authentication Tag**: Detects tampering
6. **Steganography**: Hides existence of communication

## 📊 Capacity Guidelines

Image capacity depends on dimensions:

| Image Size | Capacity |
|------------|----------|
| 800×600 | ~540 KB |
| 1920×1080 | ~2.8 MB |
| 3840×2160 (4K) | ~11 MB |

**Note**: Keep embedding rate below 10% for better stealth.

## ⚠️ Important Notes

### Image Format
- **✅ Use PNG**: Lossless compression preserves hidden data
- **❌ Avoid JPEG**: Lossy compression destroys hidden data
- **❌ Avoid resizing**: Changes pixel values

### Password Security
- Use strong passwords (12+ characters)
- Include uppercase, lowercase, numbers, symbols
- Never reuse passwords
- Store securely (password manager recommended)

### Operational Security
- Share stego images through normal channels
- Use innocent-looking cover images
- Vary cover images to avoid patterns
- Don't advertise use of steganography

## 🎓 Educational Purpose

This project demonstrates:
- Symmetric encryption (AES-256-GCM)
- Key derivation (PBKDF2)
- Steganography techniques (LSB)
- Cryptographic protocols
- Security engineering principles

## 📚 Documentation

- [PROJECT_WALKTHROUGH.md](PROJECT_WALKTHROUGH.md) - Comprehensive technical guide
- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - Project organization
- [QUICK_START.md](QUICK_START.md) - Implementation guide

## 🛠️ Future Enhancements

- [ ] DCT-based steganography for JPEG
- [ ] Audio steganography
- [ ] GUI interface
- [ ] Public key cryptography (ECDH)
- [ ] Quality metrics (PSNR, SSIM)
- [ ] Batch processing
- [ ] Network transmission

## ⚖️ Legal & Ethical Notice

**Important**: This tool is for educational purposes and legitimate privacy protection. Use responsibly and in compliance with local laws.

## 🤝 Contributing

This is a course project for Cryptography and Network Security. Feedback and improvements welcome!

## 📄 License

Educational use only.

---

**Ghost Chat** - Invisible communication through innocent images 👻

*"The best place to hide is in plain sight."*
