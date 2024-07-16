import os
import shutil
import json
from dotenv import load_dotenv
import decode
import vissearch
import gpt4o
import bsoup

load_dotenv()

# Paths and settings
BASE_URI = 'https://api.bing.microsoft.com/v7.0/images/visualsearch'
SUBSCRIPTION_KEY = os.getenv('SUBSCRIPTION_KEY')
api_key = os.getenv('API_KEY')

num_images_to_download = 5
linkstosearch = 15

# Define paths
product_images_path = "./static/product_images"
barcodes_path = "./static/barcodes"
results_folder = "./results"
archive_folder = "./archive"

# Ensure paths exist or create them
os.makedirs(product_images_path, exist_ok=True)
os.makedirs(barcodes_path, exist_ok=True)
os.makedirs(results_folder, exist_ok=True)
os.makedirs(archive_folder, exist_ok=True)

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
            bsoup.download_images(identified_product, os.path.join(results_folder, identified_product, "images"), num_images_to_download)

            # Extract information
            information = gpt4o.extract_product_data(api_key, identified_product)
            if information == "":
                information = gpt4o.extract_product_data_from_web(identified_product, api_key, linkstosearch)
        else:
            # If it has information on the product
            information = identified_product
            identified_product_name = json.loads(identified_product).get("product_name")
            identified_product_folder = os.path.join(results_folder, identified_product_name)

            # Create a subfolder for the identified product if it doesn't exist
            os.makedirs(identified_product_folder, exist_ok=True)

            # Save information as JSON file
            with open(os.path.join(identified_product_folder, "information.json"), "w") as json_file:
                json.dump(information, json_file, indent=4)

            # Download images to the subfolder
            bsoup.download_images(identified_product_name,os.path.join(identified_product_folder, "images"), num_images_to_download)

        # Move processed image to archive
        shutil.move(image_path, os.path.join(archive_folder, "product_images", image_name))

def process_barcodes():
    for image_name in os.listdir(barcodes_path):
        image_path = os.path.join(barcodes_path, image_name)
        identified_product = ""

        # Barcode identification
        ean = decode.decode_barcode(image_path)
        print("\n\n\n\nDEBUG----------------------------------", ean, "---------------------------\n\n\n\n")

        comb_links = bsoup.search_ean(ean)
        print("\n\n\n\nDEBUG----------------------------------", comb_links, "---------------------------\n\n\n\n")

        identified_product = gpt4o.identify_product(comb_links, api_key)
        print("\n\n\n\nDEBUG----------------------------------", identified_product, "---------------------------\n\n\n\n")

        # Extract information
        information = gpt4o.extract_product_data(api_key, identified_product)
        if information == "":
            information = gpt4o.extract_product_data_from_web(identified_product, api_key, linkstosearch)

        # If it has information on the product
        if identified_product != "":
            identified_product_name = json.loads(identified_product).get("product_name")
            identified_product_folder = os.path.join(results_folder, identified_product_name)

            # Create a subfolder for the identified product if it doesn't exist
            os.makedirs(identified_product_folder, exist_ok=True)

            # Save information as JSON file
            with open(os.path.join(identified_product_folder, "information.json"), "w") as json_file:
                json.dump(information, json_file, indent=4)

            # Download images to the subfolder
            bsoup.download_images(identified_product_name,os.path.join(identified_product_folder, "images"), num_images_to_download)

        # Move processed image to archive
        shutil.move(image_path, os.path.join(archive_folder, "barcodes", image_name))

if __name__ == "__main__":
    process_product_images()
    process_barcodes()
