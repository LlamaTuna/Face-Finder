from PIL import Image
import pillow_heif  # Import to enable HEIC handling in PIL
import os
import logging
import numpy as np

logger = logging.getLogger(__name__)

class ImageLoader:
    """
    A class to handle loading and validating image files, including HEIC format.
    """
    
    def __init__(self):
        self.valid_extensions = ['.png', '.jpeg', '.jpg', '.bmp', '.heic']

    def is_valid_image_extension(self, file_path):
        """
        Check if the given file path has a valid image extension.
        """
        ext = os.path.splitext(file_path)[-1].lower()
        return ext in self.valid_extensions

class ImageLoader:
    def load_image(self, image_path):
        """
        Loads an image using PIL, handles HEIC if necessary, and converts it to a NumPy array.
        """
        try:
            # Open the image file
            image = Image.open(image_path)
            image = image.convert("RGB")  # Convert to RGB for MTCNN
            image_np = np.array(image)  # Convert to NumPy array
            return image_np
        except Exception as e:
            logger.exception(f"Error loading image {image_path}: {str(e)}")
            return None
