import decode
import vissearch
import gpt4o
import bsoup
import os
from dotenv import load_dotenv
import json

load_dotenv()

# Bing API
BASE_URI = 'https://api.bing.microsoft.com/v7.0/images/visualsearch'
SUBSCRIPTION_KEY = os.getenv('SUBSCRIPTION_KEY')
api_key = os.getenv('API_KEY')

product_images_path = "./static/product_images"
barcodes_path = "./static/barcodes"
save_folder = "images"
num_images_to_download = 5
linkstosearch = 15

def process_product_images():
    for image_name in os.listdir(product_images_path):
        image_path = os.path.join(product_images_path, image_name)
        identified_product = ""

        # Identify product using GPT-4
        identified_product = gpt4o.extract_product_data(api_key, image_path=image_path)

        if identified_product == "":
            # Visual search image identification
            combstr = vissearch.vistonames(image_path, SUBSCRIPTION_KEY, BASE_URI)
            print("\n\n\n\nDEBUG----------------------------------", combstr, "---------------------------\n\n\n\n")

            identified_product = gpt4o.identify_product(combstr, api_key)
            print("\n\n\n\nDEBUG----------------------------------", identified_product, "---------------------------\n\n\n\n")

            # Download images
            bsoup.download_images(identified_product, identified_product, save_folder, num_images_to_download)

            # Extract information
            # If GPT-4 does not know, extract info from web
            if gpt4o.extract_product_data(api_key, identified_product) == "":
                gpt4o.extract_product_data_from_web(identified_product, api_key, linkstosearch)
        else:
            # If it has information on the product
            information = identified_product
            identified_product = json.loads(identified_product).get("product_name")
            bsoup.download_images(identified_product, identified_product, save_folder, num_images_to_download)

def process_barcodes():
    for image_name in os.listdir(barcodes_path):
        image_path = os.path.join(barcodes_path, image_name)

        # Barcode identification
        ean = decode.decode_barcode(image_path)
        print("\n\n\n\nDEBUG----------------------------------", ean, "---------------------------\n\n\n\n")

        comb_links = bsoup.search_ean(ean)
        print("\n\n\n\nDEBUG----------------------------------", comb_links, "---------------------------\n\n\n\n")

        identified_product = gpt4o.identify_product(comb_links, api_key)
        print("\n\n\n\nDEBUG----------------------------------", identified_product, "---------------------------\n\n\n\n")

        # Download images
        bsoup.download_images(identified_product, identified_product, save_folder, num_images_to_download)

        # Extract information
        # If GPT-4 does not know, extract info from web
        if gpt4o.extract_product_data(api_key, identified_product) == "":
            gpt4o.extract_product_data_from_web(identified_product, api_key, linkstosearch)

if __name__ == "__main__":
    process_product_images()
    process_barcodes()
