

import os
import shutil
import json
from dotenv import load_dotenv
import decode
import vissearch
import gpt4o
import bsoup
import streamlit as st

load_dotenv()
st.title('My Streamlit App')

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
os.makedirs(os.path.join(archive_folder, "product_images"), exist_ok=True)
os.makedirs(os.path.join(archive_folder, "barcodes"), exist_ok=True)

# Track processed products in this session
processed_products = []

def is_valid_ean13(ean):
    if len(ean) != 13 or not ean.isdigit():
        return False
    odd_sum = sum(int(ean[i]) for i in range(0, 12, 2))
    even_sum = sum(int(ean[i]) for i in range(1, 12, 2))
    check_digit = (10 - (odd_sum + 3 * even_sum) % 10) % 10
    return check_digit == int(ean[-1])

def process_ean(ean):
    global processed_products
    comb_links = bsoup.search_ean(ean)
    identified_product = gpt4o.identify_product(comb_links, api_key)

    # Extract information
    information = gpt4o.extract_product_data(api_key, identified_product)
    if information == "":
        information = gpt4o.extract_product_data_from_web(identified_product, api_key, linkstosearch)

    identified_product_folder = os.path.join(results_folder, identified_product)

    # Create a subfolder for the identified product if it doesn't exist
    os.makedirs(identified_product_folder, exist_ok=True)

    # Save information as JSON file
    with open(os.path.join(identified_product_folder, "information.json"), "w") as json_file:
        json.dump(information, json_file, indent=4)

    # Download images to the subfolder
    bsoup.download_images(identified_product, os.path.join(identified_product_folder, "images"),
                          num_images_to_download)
    
    # Track processed product
    processed_products.append(identified_product)

def process_product_images():
    global processed_products
    identified_product = ""
    for image_name in os.listdir(product_images_path):
        image_path = os.path.join(product_images_path, image_name)

        # Identify product using GPT-4
        information = gpt4o.extract_product_data(api_key, image_path=image_path)

        if information == "":
            # Visual search image identification
            combstr = vissearch.vistonames(image_path, SUBSCRIPTION_KEY, BASE_URI)
            identified_product = gpt4o.identify_product(combstr, api_key)

            identified_product_folder = os.path.join(results_folder, identified_product)

            # Create a subfolder for the identified product if it doesn't exist
            os.makedirs(identified_product_folder, exist_ok=True)

            # Extract information
            information = gpt4o.extract_product_data(api_key, identified_product)
            if information == "":
                information = gpt4o.extract_product_data_from_web(identified_product, api_key, linkstosearch)

            with open(os.path.join(identified_product_folder, "information.json"), "w") as json_file:
                json.dump(information, json_file, indent=4)
            # Download images
            bsoup.download_images(identified_product, os.path.join(results_folder, identified_product, "images"),
                                  num_images_to_download)
        else:
            identified_product_name = json.loads(information).get("product_name")
            identified_product_folder = os.path.join(results_folder, identified_product_name)

            # Create a subfolder for the identified product if it doesn't exist
            os.makedirs(identified_product_folder, exist_ok=True)

            # Save information as JSON file
            with open(os.path.join(identified_product_folder, "information.json"), "w") as json_file:
                json.dump(information, json_file, indent=4)
            # Download images to the subfolder
            bsoup.download_images(identified_product_name, os.path.join(identified_product_folder, "images"),
                                  num_images_to_download)
            identified_product = identified_product_name

        # Move processed image to archive
        shutil.move(image_path, os.path.join(archive_folder, "product_images", image_name))
        
        # Track processed product
        processed_products.append(identified_product)


def process_barcodes():
    global processed_products
    for image_name in os.listdir(barcodes_path):
        image_path = os.path.join(barcodes_path, image_name)

        # Barcode identification
        ean = decode.decode_barcode(image_path)
        comb_links = bsoup.search_ean(ean)
        identified_product = gpt4o.identify_product(comb_links, api_key)

        # Extract information
        information = gpt4o.extract_product_data(api_key, identified_product)
        if information == "":
            information = gpt4o.extract_product_data_from_web(identified_product, api_key, linkstosearch)

        identified_product_folder = os.path.join(results_folder, identified_product)

        # Create a subfolder for the identified product if it doesn't exist
        os.makedirs(identified_product_folder, exist_ok=True)

        # Save information as JSON file
        with open(os.path.join(identified_product_folder, "information.json"), "w") as json_file:
            json.dump(information, json_file, indent=4)

        # Download images to the subfolder
        bsoup.download_images(identified_product, os.path.join(identified_product_folder, "images"),
                              num_images_to_download)

        # Move processed image to archive
        shutil.move(image_path, os.path.join(archive_folder, "barcodes", image_name))
        
        # Track processed product
        processed_products.append(identified_product)


def save_uploaded_file(uploaded_file, save_path):
    try:
        with open(save_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())
        return True
    except Exception as e:
        st.error(f"Error: {e}")
        return False


def display_product_info(product_folder):
    info_path = os.path.join(results_folder, product_folder, "information.json")
    if os.path.exists(info_path):
        with open(info_path, "r") as json_file:
            info_data = json.load(json_file)
            st.subheader(f"Product Information for {product_folder}")
            st.json(info_data)
    else:
        st.warning(f"No information found for {product_folder}")


def display_product_images(product_folder):
    images_path = os.path.join(results_folder, product_folder, "images")
    if os.path.exists(images_path):
        st.subheader(f"Images for {product_folder}")
        image_files = os.listdir(images_path)
        for image_file in image_files:
            image_path = os.path.join(images_path, image_file)
            st.image(image_path, caption=image_file)
    else:
        st.warning(f"No images found for {product_folder}")


if __name__ == "__main__":
    st.write('Hello, welcome to my Streamlit app!')
    uploaded_files = st.file_uploader('Choose a file to upload product image', accept_multiple_files=True)
    desired_directory = product_images_path
    if st.button('Save File', key="Button1"):
        for uploaded_file in uploaded_files:
            if uploaded_file is not None:
                save_path = os.path.join(desired_directory, uploaded_file.name)
                if save_uploaded_file(uploaded_file, save_path):
                    st.success(f"File saved successfully: {save_path}")
                else:
                    st.error("Failed to save the file.")
            else:
                st.warning("No file uploaded.")

    uploaded_files = st.file_uploader('Choose a file to upload barcode image', accept_multiple_files=True)
    desired_directory = barcodes_path
    if st.button('Save File', key="Button2"):
        for uploaded_file in uploaded_files:
            if uploaded_file is not None:
                save_path = os.path.join(desired_directory, uploaded_file.name)
                if save_uploaded_file(uploaded_file, save_path):
                    st.success(f"File saved successfully: {save_path}")
                else:
                    st.error("Failed to save the file.")
            else:
                st.warning("No file uploaded.")

    if st.button("Process Files"):
        process_product_images()
        process_barcodes()

    # EAN input and processing
    ean_input = st.text_input("Enter EAN-13 number")
    if st.button("Process EAN"):
        if is_valid_ean13(ean_input):
            process_ean(ean_input)
            st.success(f"Successfully processed EAN: {ean_input}")
        else:
            st.error("Invalid EAN-13 number. Please check the input.")

    # Display information and images for processed products in this session
    for product_folder in processed_products:
        display_product_info(product_folder)
        display_product_images(product_folder)
