from PIL import Image
import requests
from io import BytesIO

def merge_images_with_spacing(image1_source, image2_source, output_path, spacing=60, upscale_to_height=2160):
    # Load images
    img1 = load_image(image1_source).convert("RGBA")
    img2 = load_image(image2_source).convert("RGBA")

    # Resize both images to a large (4K-style) height
    img1 = resize_to_height(img1, upscale_to_height)
    img2 = resize_to_height(img2, upscale_to_height)

    # Calculate combined width with spacing
    total_width = img1.width + img2.width + spacing

    # Create a transparent background canvas
    new_image = Image.new("RGBA", (total_width, upscale_to_height), (0, 0, 0, 0))

    # Paste the images with spacing
    new_image.paste(img1, (0, 0), img1)
    new_image.paste(img2, (img1.width + spacing, 0), img2)

    # Save as high-quality PNG (preserves transparency)
    new_image.save(output_path, format="PNG")
    print(f"✅ Saved combined 4K-style image to {output_path}")

def load_image(source):
    if isinstance(source, str) and source.startswith("http"):
        response = requests.get(source)
        return Image.open(BytesIO(response.content))
    return Image.open(source)

def resize_to_height(img, height):
    ratio = height / img.height
    width = int(img.width * ratio)
    return img.resize((width, height), Image.LANCZOS)

# Example usage
merge_images_with_spacing(
    "rumi-limited.png",
    "jinu-limited.png",
    "output.png",
    spacing=1,
    upscale_to_height=2160  # This makes the image 4K vertical resolution
)
