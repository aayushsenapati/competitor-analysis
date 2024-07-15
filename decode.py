import cv2
from pyzbar.pyzbar import decode

def decode_barcode(image_path):
    """
    Decodes the barcode in the given image file.

    Args:
        image_path (str): Path to the image file containing the barcode.

    Returns:
        str: The decoded EAN from the barcode, or None if no barcode is found.
    """
    # Load the image
    img = cv2.imread(image_path)

    # Decode the barcode
    decoded_objects = decode(img)

    # Extract the barcode data
    if decoded_objects:
        for obj in decoded_objects:
            if obj.type == 'EAN13' or obj.type == 'EAN8':
                return obj.data.decode("utf-8")
    return None