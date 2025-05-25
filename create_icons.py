from PIL import Image
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_mic_icon():
    """Convert mic.png to mic.ico with multiple sizes"""
    try:
        # Create icons directory if it doesn't exist
        icons_dir = 'icons'
        if not os.path.exists(icons_dir):
            os.makedirs(icons_dir)
            logger.info(f"Created icons directory: {icons_dir}")

        # Load the PNG file
        png_path = os.path.join(icons_dir, 'mic.png')
        if not os.path.exists(png_path):
            logger.error(f"mic.png not found at: {png_path}")
            return False

        # Open the PNG image
        img = Image.open(png_path)
        
        # Create a list of sizes for the ICO file
        sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        
        # Create resized versions of the image
        resized_images = []
        for size in sizes:
            resized = img.resize(size, Image.Resampling.LANCZOS)
            resized_images.append(resized)
        
        # Save as ICO file
        ico_path = os.path.join(icons_dir, 'mic.ico')
        resized_images[0].save(
            ico_path,
            format='ICO',
            sizes=[(img.width, img.height) for img in resized_images],
            append_images=resized_images[1:]
        )
        
        logger.info(f"Successfully created mic.ico at: {ico_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to create mic.ico: {e}")
        return False

if __name__ == "__main__":
    create_mic_icon() 