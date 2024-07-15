import requests
import json
from bs4 import BeautifulSoup
import os
import urllib.request

# Search for the EAN number on Google and get the top 5 links' text
def search_ean(ean_number):
    base_url = "https://www.google.com/search?q="
    search_query = f"{ean_number}"
    search_url = base_url + search_query.replace(" ", "+")
    response = requests.get(search_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    links = []
    for link in soup.find_all('a'):
        if 'href' in link.attrs and '/url?q=' in link['href'] and '/search' not in link['href']:
            actual_url = link['href'].split('/url?q=')[1].split('&')[0]
            if not actual_url.endswith(('.jpg', '.png', '.gif')) and 'google.com' not in actual_url and 'youtube.com' not in actual_url:
                links.append(link.get_text().strip())
                if len(links) >= 5:
                    break
    
    return " ".join(links)



# Fetch image URLs from Bing Image Search
def fetch_image_urls(search_term,num_images_to_download):
    headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    url = f"https://www.bing.com/images/search?q={search_term}&first=1"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')
    img_tags = soup.find_all('img', class_='mimg')

    img_urls = []
    for img in img_tags:
        img_urls.append(img.get('src'))

    return img_urls[:num_images_to_download]


#download images into images folder

def download_images(search_term,savename,save_folder,num_images_to_download):
    os.makedirs(save_folder, exist_ok=True)
    img_urls=fetch_image_urls(search_term,num_images_to_download)
    for idx, img_url in enumerate(img_urls):
        try:
            image_path = os.path.join(save_folder, f"{savename}_{idx+1}.jpg")
            urllib.request.urlretrieve(img_url, image_path)
            print(f"Downloaded image {idx+1} to {image_path}")
        except Exception as e:
            print(f"Failed to download image {idx+1}: {str(e)}")


def is_accessible_link(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return True
        else:
            print(f"Link {url} returned status code {response.status_code}. Skipping.")
            return False
    except Exception as e:
        print(f"Error checking accessibility of {url}: {e}")
        return False

def search_brand_campaigns(brand,links_per_brand):
    base_url = "https://www.google.com/search?q="
    links = []    
    print(f"Searching for campaigns for {brand}...")
    brand_links = 0  # Reset the link counter for the brand
    try:
        # Construct the search query with specific keywords related to advertisement campaigns
        search_query = f"{brand} information"
        search_url = base_url + search_query.replace(" ", "+")
        response = requests.get(search_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all links in the search results
        for link in soup.find_all('a'):
            if 'href' in link.attrs and '/url?q=' in link['href'] and '/search' not in link['href']:
                actual_url = link['href'].split('/url?q=')[1].split('&')[0]
                # Check if the link is accessible and meets the brand criteria
                if is_accessible_link(actual_url):
                    print(f"Found link: {actual_url}")
                    links.append(actual_url)
                    brand_links += 1
                    if brand_links >= links_per_brand:
                        break
    except Exception as e:
        print(f"Error occurred while searching for {brand}: {e}")
    
    return links








