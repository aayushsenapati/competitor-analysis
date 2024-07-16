import requests
from bs4 import BeautifulSoup
import bsoup
from openai import OpenAI
import base64

def identify_product(concatenated_texts,api_key):
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": f"Identify the product from the following concatenated link texts: {concatenated_texts} and return the product name(also return it in such a way that it is a safe file name) Only return this and nothing else"
            }
        ],
        max_tokens=300,
    )
    return response.choices[0].message.content

def extract_data_from_links(links,client):
    try:
        with open('content.txt', 'w', encoding='utf-8') as file:  # Open in 'w' mode to start fresh
            for i, link in enumerate(links):
                try:
                    print(f"Getting content from link {i+1}: {link}...")
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                    }
                    
                    response = requests.get(link, headers=headers)
                    soup = BeautifulSoup(response.content, 'html.parser')
                    text = soup.get_text()
                    text= "from the following content give information on company_name, product_name, product_cost, product_description,calories and ingredients if information cannot be found for that field return NA,be smart and extract as much relevant information as possible return as a json string well formatted(ensure it is just key followed by a string no arrays etc)" + text
                    
                    # Pass text to OpenAI for extraction
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": text},
                                ],
                            }
                        ],
                        max_tokens=300,
                    )

                    extracted_text = response.choices[0].message.content.strip()
                    print("Extracted text:", extracted_text)

                    # Append the extracted text to content.txt
                    file.write(extracted_text)
                    file.write(f'\n\n--- Link {i+1} End ---\n\n')

                except Exception as e:
                    print(f"Error occurred while processing {link}: {e}")
                    
        print("Finished writing content to content.txt")

    except Exception as e:
        print(f"Error writing to content.txt: {e}")

def extract_product_data_from_web(product,api_key,linkstosearch):
    try:
        client = OpenAI(api_key=api_key)
        links=bsoup.search_brand_campaigns(product,linkstosearch)
        extract_data_from_links(links,client)
        with open('content.txt', 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Pass content to ChatGPT for final extraction
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"""Given the following data on brand campaigns, I want you to extract info on the following columns: company_name, product_name, product_cost, product_description,calories(convert to calories if necessary) and ingredients. 
                            Be smart and extract the brand-related data from all the nonsense you get; if you can't find a relevant thing, replace it with 'NA'.
                            Read through content carefully and try your best to place all information from all the links in the following content.You have a tendency to forget to include information from some links,so try and be as descriptive as possible and inclure all valid content for description and ingredients calories etc .I want to avoid Na's unless necessary. 
                            Keep the following in mind very carefully, the response should only have results of a single BRAND, no other data should be included. The company_name column must describe the name of the company.
                             Also, if you feel some links are not relevant to most of the other links ,ignore information from those links.So try and fill the json with the most likely product's information.
                             The product_name should be the name of the product associated with the brand. The product_cost should be the cost of the product and not any other cost. 
                              The response should always be in JSON format. Always return all columns in the JSON object, and if you cannot find relevant data, return 'NA'.
                              All the keys should be in snake_case. Be sure to give me only 1 JSON object, with no nested objects or arrays. Per column, only include 1 value.
                              You have a tendency to forget to include information from some links,so try and be as descriptive as possible and inclure all valid content for description and ingredients calories etc .
                              """,
                        },
                        {
                            "type": "text",
                            "text": content,
                        },
                    ],
                }
            ],
            max_tokens=300,
        )

        extracted_data = response.choices[0].message.content.strip()
        print("Extracted data:", extracted_data)
        lines = extracted_data.splitlines()[1:-1]
        cleaned_data = '\n'.join(lines).strip()
        return cleaned_data

    except Exception as e:
        print(f"Error extracting brand data from content.txt: {e}")

def extract_product_data(api_key,identified_product=None,image_path=None):
    client = OpenAI(api_key=api_key)
    variation=None
    if identified_product is None:
        with open(image_path, "rb") as image_file:
            base64_im=base64.b64encode(image_file.read()).decode('utf-8')
        variation=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_im}",
                            },
                        },
                        {
                            "type": "text",
                            "text": f"for the above image extract the following columns if you have information on this product(the exact same product in the image),so if you dont have any idea on this specific product please return the number 0 and nothing else. I dont want you to return any hallucinations,if you don't know the product or can't clearly see the product just return 0,",
                        },
                        {
                            "type": "text",
                            "text": f"""company_name, product_name, product_cost, product_description,calories and ingredients if information cannot be found for that field return NA,be smart and extract as much relevant information as possible return as a VALID json string correctly formatted(ensure it is just key followed by a string, no arrays,nested arrays etc)
                              ensure product name is a safe file name format so i can use it directly in a file name
                              """,
                        },
                    ],
                }
            ]
    elif image_path is None:
        variation=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"given this product {identified_product} extract the following columns if you have information on this product(the exact product not any variation of it), I dont want you to return any hallucinations,so if you dont have any idea on this specific product please return the number 0 and nothing else. I dont want you to return any hallucinations,if you don't know the product just return 0",
                        },
                        {
                            "type": "text",
                            "text": f"""company_name, product_name, product_cost, product_description,calories and ingredients if information cannot be found for that field return NA,be smart and extract as much relevant information as possible return as a VALID json string correctly formatted(ensure it is just key followed by a string no arrays,nested arrays etc)
                              ensure product name is a safe file name format so i can use it directly in a file name
                              """,
                        },
                    ],
                }
            ]

    
    response = client.chat.completions.create(
            model="gpt-4o",
            messages=variation,
            max_tokens=300,
        )
    extracted_data = response.choices[0].message.content.strip()
    print("Extracted data:", extracted_data)
    if extracted_data == "0":
        return ""
    else:
        lines = extracted_data.splitlines()[1:-1]
        cleaned_data = '\n'.join(lines).strip()
        return cleaned_data
