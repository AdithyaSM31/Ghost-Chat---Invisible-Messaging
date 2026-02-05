"""
Create test images for Ghost Chat testing
"""

from PIL import Image, ImageDraw, ImageFont
import random
from pathlib import Path


def create_solid_color_image(width=800, height=600, filename="solid.png"):
    """Create a solid color image"""
    img = Image.new('RGB', (width, height), color=(100, 150, 200))
    img.save(filename)
    print(f"✅ Created {filename} ({width}×{height})")


def create_gradient_image(width=800, height=600, filename="gradient.png"):
    """Create a gradient image"""
    img = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(img)
    
    for y in range(height):
        r = int(255 * (y / height))
        g = int(150 * (1 - y / height))
        b = int(200 * (y / height))
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    img.save(filename)
    print(f"✅ Created {filename} ({width}×{height})")


def create_random_noise_image(width=800, height=600, filename="noise.png"):
    """Create a random noise image"""
    img = Image.new('RGB', (width, height))
    pixels = img.load()
    
    for y in range(height):
        for x in range(width):
            pixels[x, y] = (
                random.randint(0, 255),
                random.randint(0, 255),
                random.randint(0, 255)
            )
    
    img.save(filename)
    print(f"✅ Created {filename} ({width}×{height})")


def create_pattern_image(width=800, height=600, filename="pattern.png"):
    """Create a checkered pattern image"""
    img = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(img)
    
    square_size = 50
    colors = [(200, 100, 100), (100, 200, 100)]
    
    for y in range(0, height, square_size):
        for x in range(0, width, square_size):
            color_idx = ((x // square_size) + (y // square_size)) % 2
            draw.rectangle(
                [x, y, x + square_size, y + square_size],
                fill=colors[color_idx]
            )
    
    img.save(filename)
    print(f"✅ Created {filename} ({width}×{height})")


def create_text_image(width=800, height=600, filename="text.png"):
    """Create an image with text"""
    img = Image.new('RGB', (width, height), color=(240, 240, 240))
    draw = ImageDraw.Draw(img)
    
    # Draw some text
    texts = [
        "This is a cover image",
        "It looks completely innocent",
        "But it might hide secrets...",
        "Ghost Chat Steganography Test"
    ]
    
    y_position = 100
    for text in texts:
        # Use default font
        draw.text((50, y_position), text, fill=(50, 50, 50))
        y_position += 100
    
    # Add some decorative elements
    for _ in range(20):
        x = random.randint(0, width)
        y = random.randint(0, height)
        r = random.randint(10, 30)
        color = (random.randint(100, 200), random.randint(100, 200), random.randint(100, 200))
        draw.ellipse([x-r, y-r, x+r, y+r], fill=color)
    
    img.save(filename)
    print(f"✅ Created {filename} ({width}×{height})")


def main():
    """Create all test images"""
    print("=" * 60)
    print("Creating Test Images for Ghost Chat")
    print("=" * 60)
    
    # Create data directory if it doesn't exist
    output_dir = Path("data/cover_images")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\nOutput directory: {output_dir}")
    print()
    
    # Create various test images
    sizes = [
        (800, 600, "small"),
        (1920, 1080, "medium"),
        (3840, 2160, "large")
    ]
    
    for width, height, size_name in sizes:
        print(f"\nCreating {size_name} images ({width}×{height}):")
        create_solid_color_image(width, height, 
            output_dir / f"solid_{size_name}.png")
        create_gradient_image(width, height, 
            output_dir / f"gradient_{size_name}.png")
        
        # Only create noise and pattern for smaller sizes (faster)
        if size_name == "small":
            create_random_noise_image(width, height, 
                output_dir / f"noise_{size_name}.png")
            create_pattern_image(width, height, 
                output_dir / f"pattern_{size_name}.png")
            create_text_image(width, height, 
                output_dir / f"text_{size_name}.png")
    
    print("\n" + "=" * 60)
    print("✅ All test images created successfully!")
    print("=" * 60)
    
    # Calculate capacities
    print("\n📊 Image Capacities:")
    for width, height, size_name in sizes:
        capacity = ((width * height * 3) - 32) // 8
        print(f"   {size_name.capitalize()} ({width}×{height}): {capacity:,} bytes ({capacity / 1024:.2f} KB)")
    
    print(f"\n💡 Test images saved to: {output_dir}")
    print("   You can now use these images with ghost_chat.py")


if __name__ == "__main__":
    main()
