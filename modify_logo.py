import os
import sys
from PIL import Image, ImageDraw
import requests
from io import BytesIO

def create_svg_icon():
    # SVG template for Al Fakher logo with red background and outline
    svg_content = '''<svg width="150" height="150" xmlns="http://www.w3.org/2000/svg">
    <!-- Red background rectangle -->
    <rect x="20" y="20" width="110" height="110" rx="10" ry="10" fill="#ffeeee" stroke="red" stroke-width="5"/>
    
    <!-- Al Fakher Text -->
    <text x="75" y="75" font-family="Arial" font-size="24" font-weight="bold" text-anchor="middle" dominant-baseline="middle">AF</text>
</svg>'''
    
    # Save the SVG file
    with open('al_fakher_icon.svg', 'w') as f:
        f.write(svg_content)
    
    print("Created al_fakher_icon.svg with red outline")

def download_and_modify_image():
    try:
        # URL of the Al Fakher logo
        image_url = "https://images.squarespace-cdn.com/content/v1/66b4885f1e86da03215efed0/d697e610-2cf8-40fe-86a0-7438326dcdeb/AlFakher_logo.png?format=1500w"
        
        # Download the image
        response = requests.get(image_url)
        response.raise_for_status()  # Raise exception for HTTP errors
        
        # Open the image
        img = Image.open(BytesIO(response.content))
        
        # Create a new image with transparent background for the outline
        outline_img = Image.new('RGBA', img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(outline_img)
        
        # Draw red outline around the edge of the image
        outline_width = 10  # Width of the outline
        draw.rectangle(
            [(0, 0), (img.width - 1, img.height - 1)],
            outline='red',
            width=outline_width
        )
        
        # Combine the original image with the outline
        result = Image.alpha_composite(outline_img, img.convert('RGBA'))
        
        # Save the result
        result.save('al_fakher_red_outline.png')
        
        print("Created al_fakher_red_outline.png with red outline")
        return True
    except Exception as e:
        print(f"Error modifying image: {e}")
        return False

if __name__ == "__main__":
    # First try to download and modify the real image
    success = download_and_modify_image()
    
    # If that fails, create an SVG alternative
    if not success:
        create_svg_icon()