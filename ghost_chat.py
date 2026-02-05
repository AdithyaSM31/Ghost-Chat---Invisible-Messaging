"""
Ghost Chat - Steganographic Messenger
Main CLI application

Hide encrypted messages in images to achieve deniable authenticity
and avoid metadata profiling in communication.
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
    print("=" * 60)
    print("🔐 GHOST CHAT - HIDE MESSAGE")
    print("=" * 60)
    
    # Display operation info
    print(f"\n📝 Message: {args.message[:50]}{'...' if len(args.message) > 50 else ''}")
    print(f"🖼️  Cover image: {Path(args.image).name}")
    print(f"💾 Output: {Path(args.output).name}")
    
    try:
        # Step 1: Encrypt message
        print("\n" + "-" * 60)
        print("Step 1/3: Encrypting message with AES-256-GCM...")
        encryptor = MessageEncryptor(args.password)
        encrypted = encryptor.encrypt(args.message)
        print(f"✅ Message encrypted ({len(encrypted['ciphertext'])} bytes)")
        
        # Step 2: Pack into protocol format
        print("\n" + "-" * 60)
        print("Step 2/3: Packing into Ghost protocol format...")
        packed = GhostProtocol.pack(encrypted)
        print(f"✅ Message packed ({len(packed)} bytes total)")
        print(f"   📦 Header: {GhostProtocol.HEADER_SIZE} bytes")
        print(f"   🔒 Ciphertext: {len(encrypted['ciphertext'])} bytes")
        print(f"   🏷️  Tag: {GhostProtocol.TAG_SIZE} bytes")
        
        # Step 3: Embed in image
        print("\n" + "-" * 60)
        print("Step 3/3: Embedding in image using LSB steganography...")
        stego = LSBSteganography(args.image)
        
        # Check capacity
        capacity = stego.calculate_capacity()
        print(f"   Image capacity: {capacity:,} bytes ({capacity / 1024:.2f} KB)")
        print(f"   Data size: {len(packed):,} bytes ({len(packed) / 1024:.2f} KB)")
        
        if len(packed) > capacity:
            print(f"\n❌ ERROR: Message too large for image!")
            print(f"   Required: {len(packed):,} bytes")
            print(f"   Available: {capacity:,} bytes")
            print(f"   Shortage: {len(packed) - capacity:,} bytes")
            print(f"\n💡 Try using a larger image or shorter message.")
            return
        
        # Embed the data
        stego.embed(packed, args.output)
        
        # Show final statistics
        print("\n" + "=" * 60)
        print("✅ SUCCESS!")
        print("=" * 60)
        
        original_size = Path(args.image).stat().st_size
        stego_size = Path(args.output).stat().st_size
        
        print(f"\n📊 Statistics:")
        print(f"   Original image: {original_size:,} bytes ({original_size / 1024:.2f} KB)")
        print(f"   Stego image: {stego_size:,} bytes ({stego_size / 1024:.2f} KB)")
        print(f"   Hidden data: {len(packed):,} bytes ({len(packed) / 1024:.2f} KB)")
        print(f"   Capacity used: {len(packed) / capacity * 100:.2f}%")
        
        print(f"\n💾 Stego image saved to: {args.output}")
        print(f"\n🔒 Keep your password safe! You'll need it to extract the message.")
        
    except FileNotFoundError as e:
        print(f"\n❌ ERROR: {e}")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        if args.verbose:
            traceback.print_exc()


def extract_message(args):
    """Extract and decrypt message from stego image"""
    print("=" * 60)
    print("🔓 GHOST CHAT - EXTRACT MESSAGE")
    print("=" * 60)
    
    print(f"\n🖼️  Stego image: {Path(args.image).name}")
    
    try:
        # Step 1: Extract from image
        print("\n" + "-" * 60)
        print("Step 1/3: Extracting hidden data from image...")
        stego = LSBSteganography(args.image)
        packed = stego.extract(args.image)
        print(f"✅ Extracted {len(packed)} bytes")
        
        # Step 2: Unpack protocol message
        print("\n" + "-" * 60)
        print("Step 2/3: Unpacking Ghost protocol message...")
        try:
            encrypted = GhostProtocol.unpack(packed)
            print(f"✅ Valid Ghost protocol message detected")
            print(f"   Protocol version: {GhostProtocol.VERSION}")
        except ValueError as e:
            print(f"❌ ERROR: {e}")
            print(f"   This may not be a Ghost Chat image, or the data is corrupted.")
            return
        
        # Step 3: Decrypt
        print("\n" + "-" * 60)
        print("Step 3/3: Decrypting message...")
        encryptor = MessageEncryptor(args.password)
        try:
            message = encryptor.decrypt(encrypted)
            print(f"✅ Message decrypted successfully!")
        except ValueError:
            print(f"❌ ERROR: Decryption failed!")
            print(f"   Possible causes:")
            print(f"   - Wrong password")
            print(f"   - Corrupted data")
            print(f"   - Modified stego image")
            return
        
        # Display the message
        print("\n" + "=" * 60)
        print("✅ MESSAGE RECOVERED")
        print("=" * 60)
        print()
        print(message)
        print()
        print("=" * 60)
        
        # Save to file if requested
        if args.output:
            output_path = Path(args.output)
            output_path.write_text(message, encoding='utf-8')
            print(f"\n💾 Message saved to: {args.output}")
        
    except FileNotFoundError as e:
        print(f"\n❌ ERROR: {e}")
    except ValueError as e:
        print(f"\n❌ ERROR: {e}")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        if args.verbose:
            traceback.print_exc()


def check_capacity(args):
    """Check image capacity for hiding data"""
    print("=" * 60)
    print("📊 GHOST CHAT - IMAGE CAPACITY")
    print("=" * 60)
    
    try:
        stego = LSBSteganography(args.image)
        info = stego.get_info()
        
        print(f"\n🖼️  Image: {Path(args.image).name}")
        print(f"\n📐 Dimensions:")
        print(f"   Width: {info['width']} pixels")
        print(f"   Height: {info['height']} pixels")
        print(f"   Total pixels: {info['total_pixels']:,}")
        print(f"   Color mode: {info['mode']}")
        
        print(f"\n💾 Steganography Capacity:")
        print(f"   Maximum: {info['capacity_bytes']:,} bytes")
        print(f"           {info['capacity_kb']:.2f} KB")
        print(f"           {info['capacity_mb']:.4f} MB")
        
        # Calculate typical message sizes
        print(f"\n📝 What you can hide:")
        
        # Calculate overhead
        overhead = GhostProtocol.HEADER_SIZE + GhostProtocol.TAG_SIZE
        
        examples = [
            ("Short message (200 chars)", 200 + overhead),
            ("Tweet (280 chars)", 280 + overhead),
            ("SMS (160 chars)", 160 + overhead),
            ("Small paragraph (500 chars)", 500 + overhead),
            ("One page text (~2 KB)", 2048 + overhead),
            ("Long message (~5 KB)", 5120 + overhead),
        ]
        
        for name, size in examples:
            if size <= info['capacity_bytes']:
                percentage = (size / info['capacity_bytes']) * 100
                print(f"   ✅ {name}: {size:,} bytes ({percentage:.1f}% capacity)")
            else:
                print(f"   ❌ {name}: {size:,} bytes (TOO LARGE)")
        
        # File size info
        file_size = Path(args.image).stat().st_size
        print(f"\n📁 File Information:")
        print(f"   File size: {file_size:,} bytes ({file_size / 1024:.2f} KB)")
        print(f"   Format: {Path(args.image).suffix}")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        print(f"   - Use PNG format for steganography (lossless)")
        print(f"   - Avoid JPEG (compression destroys hidden data)")
        print(f"   - Keep embedding rate below 10% for better stealth")
        print(f"   - Larger images = more capacity")
        
    except FileNotFoundError as e:
        print(f"\n❌ ERROR: {e}")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Ghost Chat - Steganographic Messenger\n'
                    'Hide encrypted messages in images to achieve deniable authenticity.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Hide a message in an image
  python ghost_chat.py hide --image photo.png --message "Secret meeting at dawn" --password "MyPass123" --output stego.png
  
  # Extract a message from a stego image
  python ghost_chat.py extract --image stego.png --password "MyPass123"
  
  # Save extracted message to file
  python ghost_chat.py extract --image stego.png --password "MyPass123" --output message.txt
  
  # Check image capacity
  python ghost_chat.py capacity --image photo.png

Security Notes:
  - Messages are encrypted with AES-256-GCM
  - Use strong passwords (12+ characters)
  - Share stego images through normal channels (social media, email)
  - The encryption makes the hidden data look like random noise
        """
    )
    
    # Add verbose flag
    parser.add_argument('-v', '--verbose', action='store_true', 
                       help='Enable verbose output (show errors)')
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Hide command
    hide_parser = subparsers.add_parser('hide', help='Hide message in image')
    hide_parser.add_argument('--image', required=True, help='Cover image path (PNG recommended)')
    hide_parser.add_argument('--message', required=True, help='Message to hide')
    hide_parser.add_argument('--password', required=True, help='Encryption password (keep it safe!)')
    hide_parser.add_argument('--output', required=True, help='Output stego image path')
    
    # Extract command
    extract_parser = subparsers.add_parser('extract', help='Extract message from stego image')
    extract_parser.add_argument('--image', required=True, help='Stego image path')
    extract_parser.add_argument('--password', required=True, help='Decryption password')
    extract_parser.add_argument('--output', help='Save message to file (optional)')
    
    # Capacity command
    capacity_parser = subparsers.add_parser('capacity', help='Check image capacity')
    capacity_parser.add_argument('--image', required=True, help='Image path to check')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Execute command
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
