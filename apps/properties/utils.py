import os
from PIL import Image
from django.core.exceptions import ValidationError

MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp']

def validate_property_image(uploaded_file):
    """
    Validates uploaded property image for file size, extension, and Pillow integrity verification.
    """
    if uploaded_file.size > MAX_UPLOAD_SIZE:
        raise ValidationError(f"File size exceeds maximum allowed limit of 5MB (Got {uploaded_file.size / (1024*1024):.2f}MB).")

    ext = os.path.splitext(uploaded_file.name)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError(f"Unsupported file extension '{ext}'. Allowed extensions are: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}")

    try:
        img = Image.open(uploaded_file)
        img.verify()
    except Exception as e:
        raise ValidationError("Uploaded file is not a valid or uncorrupted image.") from e

    return True

def optimize_and_save_image(uploaded_file, max_width=1600, quality=85):
    """
    Resizes image if width exceeds max_width and optimizes/converts to WebP or compressed format.
    """
    try:
        img = Image.open(uploaded_file)
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')

        width, height = img.size
        if width > max_width:
            new_height = int((max_width / width) * height)
            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

        return img
    except Exception:
        return None
