/**
 * Ghost Engine - Client-Side Cryptography & Steganography
 * Allows the app to work offline without the Python backend for basic features.
 */

const GhostEngine = {
    // Protocol Constants
    MAGIC: [0x47, 0x48, 0x53, 0x54], // 'GHST'
    VERSION: 1,
    HEADER_SIZE: 68,
    TAG_SIZE: 16,
    NONCE_SIZE: 16,
    SALT_SIZE: 32,

    /**
     * Encrypts a message using AES-256-GCM
     */
    async encryptMessage(password, message) {
        const enc = new TextEncoder();
        const msgBytes = enc.encode(message);
        const passwordBytes = enc.encode(password);

        // Generate Salt & Nonce
        const salt = window.crypto.getRandomValues(new Uint8Array(32));
        const nonce = window.crypto.getRandomValues(new Uint8Array(16));

        // Derive Key (PBKDF2-SHA1 to match Python Match)
        const key = await this.deriveKey(passwordBytes, salt);

        // Encrypt
        const encryptedBuffer = await window.crypto.subtle.encrypt(
            { name: "AES-GCM", iv: nonce, tagLength: 128 },
            key,
            msgBytes
        );

        // The Web Crypto API returns Ciphertext + Tag concatenated at the end
        // Extract them
        const totalLen = encryptedBuffer.byteLength;
        const tagOffset = totalLen - 16;
        const ciphertext = new Uint8Array(encryptedBuffer.slice(0, tagOffset));
        const tag = new Uint8Array(encryptedBuffer.slice(tagOffset));

        return { salt, nonce, ciphertext, tag };
    },

    /**
     * Decrypts a packed message
     */
    async decryptMessage(password, packedBytes) {
        // Unpack
        const parts = this.unpack(packedBytes);
        if (!parts) throw new Error("Invalid Ghost Header");

        const enc = new TextEncoder();
        const passwordBytes = enc.encode(password);
        
        // Derive Key
        const key = await this.deriveKey(passwordBytes, parts.salt);

        // Reconstruct ciphertext + tag for Web Crypto
        const cipherWithTag = new Uint8Array(parts.ciphertext.length + 16);
        cipherWithTag.set(parts.ciphertext);
        cipherWithTag.set(parts.tag, parts.ciphertext.length);

        try {
            const decryptedBuffer = await window.crypto.subtle.decrypt(
                { name: "AES-GCM", iv: parts.nonce, tagLength: 128 },
                key,
                cipherWithTag
            );
            return new TextDecoder().decode(decryptedBuffer);
        } catch (e) {
            throw new Error("Wrong password or corrupted data.");
        }
    },

    /**
     * Key Derivation (Matches Python PyCryptodome default)
     */
    async deriveKey(passwordBytes, salt) {
        const baseKey = await window.crypto.subtle.importKey(
            "raw", passwordBytes, "PBKDF2", false, ["deriveKey"]
        );
        return await window.crypto.subtle.deriveKey(
            { name: "PBKDF2", salt: salt, iterations: 100000, hash: "SHA-1" },
            baseKey,
            { name: "AES-GCM", length: 256 },
            false,
            ["encrypt", "decrypt"]
        );
    },

    /**
     * Packs data into Ghost Protocol Format
     * Header: Magic(4) + Version(2) + ContentLen(4) + Salt(32) + Nonce(16) + Reserved(10)
     */
    pack(data) {
        const buffer = new ArrayBuffer(68 + data.ciphertext.length + 16);
        const view = new DataView(buffer);
        const bytes = new Uint8Array(buffer);

        let offset = 0;
        
        // Magic 'GHST'
        bytes.set(this.MAGIC, 0); offset += 4;
        
        // Version
        view.setUint16(offset, this.VERSION, false); offset += 2; // Big Endian
        
        // Ciphertext Length
        view.setUint32(offset, data.ciphertext.length, false); offset += 4;
        
        // Salt (32)
        bytes.set(data.salt, offset); offset += 32;
        
        // Nonce (16)
        bytes.set(data.nonce, offset); offset += 16;
        
        // Reserved (10) - Zeros
        offset += 10;
        
        // Encrypted Payload
        bytes.set(data.ciphertext, offset); offset += data.ciphertext.length;
        
        // Tag
        bytes.set(data.tag, offset);
        
        return bytes;
    },

    /**
     * Unpacks protocol bytes
     */
    unpack(buffer) {
        const view = new DataView(buffer.buffer ? buffer.buffer : buffer);
        const bytes = new Uint8Array(buffer.buffer ? buffer.buffer : buffer);
        
        // Check Header Size
        if (bytes.length < 68) return null;

        // Check Magic
        if (bytes[0] !== 0x47 || bytes[1] !== 0x48 || bytes[2] !== 0x53 || bytes[3] !== 0x54) return null;
        
        let offset = 4;
        const version = view.getUint16(offset, false); offset += 2;
        const cipherLen = view.getUint32(offset, false); offset += 4;
        
        const salt = bytes.slice(offset, offset + 32); offset += 32;
        const nonce = bytes.slice(offset, offset + 16); offset += 16;
        offset += 10; // Skip reserved
        
        if (bytes.length < offset + cipherLen + 16) return null; // Incomplete
        
        const ciphertext = bytes.slice(offset, offset + cipherLen); offset += cipherLen;
        const tag = bytes.slice(offset, offset + 16);
        
        return { salt, nonce, ciphertext, tag };
    },

    /**
     * LSB Steganography embedding
     */
    embedLSB(imageData, secretData) {
        const width = imageData.width;
        const height = imageData.height;
        const pixels = imageData.data;
        
        // Add 32-bit length header to secretData
        const lenBuffer = new ArrayBuffer(4);
        new DataView(lenBuffer).setUint32(0, secretData.length, false); // Big Endian
        const lenBytes = new Uint8Array(lenBuffer);
        
        const fullPayload = new Uint8Array(lenBytes.length + secretData.length);
        fullPayload.set(lenBytes);
        fullPayload.set(secretData, 4);
        
        // Calculate bit capacity (3 bits per pixel: R, G, B)
        // Alpha is preserved
        const capacityBytes = Math.floor((width * height * 3) / 8);
        if (fullPayload.length > capacityBytes) {
            throw new Error(`Data too large. Capacity: ${capacityBytes} bytes, Data: ${fullPayload.length} bytes`);
        }

        let dataIdx = 0;
        let bitIdx = 0;
        
        for (let i = 0; i < pixels.length; i += 4) {
             // Iterate RGB
             for (let j = 0; j < 3; j++) {
                 if (dataIdx >= fullPayload.length) break;
                 
                 const byte = fullPayload[dataIdx];
                 const bit = (byte >> (7 - bitIdx)) & 1;
                 
                 // Clear LSB and set new bit
                 pixels[i + j] = (pixels[i + j] & ~1) | bit;
                 
                 bitIdx++;
                 if (bitIdx === 8) {
                     bitIdx = 0;
                     dataIdx++;
                 }
             }
             if (dataIdx >= fullPayload.length) break;
        }
        
        return imageData;
    },

    /**
     * LSB Extraction
     */
    extractLSB(imageData) {
        const pixels = imageData.data;
        const bytes = [];
        let currentByte = 0;
        let bitCount = 0;
        
        // Extract first 32 bits for length
        let lengthHeader = 0;
        let lengthBitsRead = 0;
        
        let msgLen = null;
        let msgBytesRead = 0;
        
        for (let i = 0; i < pixels.length; i += 4) {
            for (let j = 0; j < 3; j++) {
                const bit = pixels[i + j] & 1;
                
                if (msgLen === null) {
                    // Reading Length
                    lengthHeader = (lengthHeader << 1) | bit;
                    lengthBitsRead++;
                    
                    if (lengthBitsRead === 32) {
                        msgLen = lengthHeader;
                        // Determine bounds
                         const capacityBytes = Math.floor((imageData.width * imageData.height * 3) / 8);
                         if (msgLen < 0 || msgLen > capacityBytes) {
                             throw new Error("Invalid steganographic header detected.");
                         }
                    }
                } else {
                    // Reading Data
                    currentByte = (currentByte << 1) | bit;
                    bitCount++;
                    
                    if (bitCount === 8) {
                        bytes.push(currentByte);
                        msgBytesRead++;
                        currentByte = 0;
                        bitCount = 0;
                        
                        if (msgBytesRead === msgLen) {
                            return new Uint8Array(bytes);
                        }
                    }
                }
            }
            if (msgLen !== null && msgBytesRead === msgLen) break;
        }
        
        throw new Error("Failed to extract complete message.");
    }
};
