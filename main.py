#import decode.py
import vissearch
import gpt4o
import bsoup
import os
from dotenv import load_dotenv
load_dotenv()


#bing api
BASE_URI = 'https://api.bing.microsoft.com/v7.0/images/visualsearch'
SUBSCRIPTION_KEY = os.getenv('SUBSCRIPTION_KEY')
api_key = os.getenv('API_KEY')



imagepath="./static/image.png"
save_folder = "images"
num_images_to_download = 5
linkstosearch=15


#visual search image identification
combstr=vissearch.vistonames(imagepath,SUBSCRIPTION_KEY,BASE_URI)
print("\n\n\n\nDEBUG----------------------------------",combstr,"---------------------------\n\n\n\n")

identified_product=gpt4o.identify_product(combstr,api_key)
print("\n\n\n\nDEBUG----------------------------------",identified_product,"---------------------------\n\n\n\n")


# barcode identification

#ean=decode.decode_barcode(imagepath)
#print("\n\n\n\nDEBUG----------------------------------",ean,"---------------------------\n\n\n\n")
#comblinks=bsoup.search_ean(ean)
#print("\n\n\n\nDEBUG----------------------------------",comblinks,"---------------------------\n\n\n\n")

#identified_product=gpt4o.identify_product(comblinks,api_key)
#print("\n\n\n\nDEBUG----------------------------------",identified_product,"---------------------------\n\n\n\n")



#download images

bsoup.download_images(identified_product,identified_product,save_folder,num_images_to_download)

#extract information
gpt4o.extract_product_data_from_web(identified_product,api_key,linkstosearch)

