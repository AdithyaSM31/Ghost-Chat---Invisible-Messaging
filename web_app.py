"""
Ghost Chat - Web Interface
Flask application to provide a modern "vibey" dark-mode frontend
"""

import os
import sys
from pathlib import Path
from flask import Flask, render_template, request, send_file, jsonify, flash, redirect, url_for
from werkzeug.utils import secure_filename
import io

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from crypto.encryption import MessageEncryptor
from protocol.ghost_protocol import GhostProtocol
from steganography.lsb_stego import LSBSteganography
from steganography.dct_stego import DCTSteganography

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 128 * 1024 * 1024  # 128MB max upload

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/encrypt_hide', methods=['POST'])
def encrypt_hide():
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image file uploaded'}), 400
        
        file = request.files['image']
        message = request.form.get('message')
        password = request.form.get('password')
        
        if not file or file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        if not password:
            return jsonify({'error': 'Password is required'}), 400
            
        # Save uploaded file momentarily
        filename = secure_filename(file.filename)
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(input_path)
        
        # Output path
        output_filename = f"stego_{filename.split('.')[0]}.png"
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
        
        # 1. Encrypt
        encryptor = MessageEncryptor(password)
        encrypted = encryptor.encrypt(message)
        
        # 2. Pack
        packed = GhostProtocol.pack(encrypted)
        
        # 3. Embed
        # Choose steganography method based on file type
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext in ['.jpg', '.jpeg']:
            stego = DCTSteganography(input_path)
            print(f"Using DCT Steganography for {filename}")
        else:
            stego = LSBSteganography(input_path)
            print(f"Using LSB Steganography for {filename}")
        
        # Check capacity
        capacity = stego.calculate_capacity()
        if len(packed) > capacity:
            os.remove(input_path)
            return jsonify({
                'error': f'Message too large! Capacity: {capacity} bytes, Data: {len(packed)} bytes'
            }), 400
            
        stego.embed(packed, output_path)
        
        # Helper to return the file download URL/Trigger
        return jsonify({
            'success': True,
            'download_url': f'/download/{output_filename}',
            'stats': {
                'original_size': os.path.getsize(input_path),
                'stego_size': os.path.getsize(output_path),
                'hidden_bytes': len(packed),
                'capacity_used': f"{(len(packed)/capacity)*100:.2f}%"
            }
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/extract_decrypt', methods=['POST'])
def extract_decrypt():
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image file uploaded'}), 400
        
        file = request.files['image']
        password = request.form.get('password')
        
        if not file or file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        if not password:
            return jsonify({'error': 'Password is required'}), 400
            
        # Save uploaded file
        filename = secure_filename(file.filename)
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(input_path)
        
        # 1. Extract
        packed = None
        extraction_errors = []
        
        # Method 1: LSB
        try:
            lsb_stego = LSBSteganography(input_path)
            candidate = lsb_stego.extract()
            if candidate.startswith(b'GHST'):
                packed = candidate
        except Exception as e:
            extraction_errors.append(f"LSB: {str(e)}")

        # Method 2: DCT (if LSB failed)
        if packed is None:
            try:
                dct_stego = DCTSteganography(input_path)
                candidate = dct_stego.extract()
                if candidate.startswith(b'GHST'):
                    packed = candidate
            except Exception as e:
                extraction_errors.append(f"DCT: {str(e)}")
                
        if packed is None:
             return jsonify({'error': f'Failed to extract data. Valid Ghost header not found.'}), 400
            
        # 2. Unpack
        try:
            encrypted = GhostProtocol.unpack(packed)
        except ValueError:
            return jsonify({'error': 'Invalid data format. Not a Ghost Chat image.'}), 400
            
        # 3. Decrypt
        encryptor = MessageEncryptor(password)
        try:
            message = encryptor.decrypt(encrypted)
        except ValueError:
            return jsonify({'error': 'Wrong password or corrupted data.'}), 400
            
        # Clean up input file
        os.remove(input_path)
        
        return jsonify({
            'success': True, 
            'message': message
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename), as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
