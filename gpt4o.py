import requests
from bs4 import BeautifulSoup
import bsoup
from openai import OpenAI
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed


def identify_product(concatenated_texts, api_key):
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


def extract_data_from_link(link, client, link_index):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(link, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        text = soup.get_text()
        text = "from the following content give information on company_name, product_name, product_cost, product_description,nutritional information and ingredients if information cannot be found for that field return NA,be smart and extract as much relevant information as possible return as a json string well formatted(ensure it is just key followed by a string no arrays etc, only nutritional should be a nested json if there is any information else for nutritional info NA)" + text

        # Pass text to OpenAI for extraction
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [

                {
                    "type": "text",
                    "text": f"""This is the master rule,dont return any other response sentences or words other than the JSON object in markdown code.
                    """,
                },
                        {"type": "text", "text": text},
                    ],
                }
            ],
        )

        extracted_text = response.choices[0].message.content.strip()
        print(f"Extracted text for link {link_index}: {extracted_text}")

        return f'{extracted_text}\n\n--- Link {link_index} End ---\n\n'
    
    except Exception as e:
        print(f"Error occurred while processing {link}: {e}")
        return None

def extract_data_from_links(links, client):
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_link = {executor.submit(extract_data_from_link, link, client, i + 1): link for i, link in enumerate(links)}
        with open('content.txt', 'w', encoding='utf-8') as file:
            for future in as_completed(future_to_link):
                result = future.result()
                if result:
                    file.write(result)

    print("Finished writing content to content.txt")



def extract_product_data_from_web(product, api_key, linkstosearch):
    try:
        client = OpenAI(api_key=api_key)
        links = bsoup.search_brand_campaigns(product, linkstosearch)
        extract_data_from_links(links, client)
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
                        "text": f"""This is the master rule,dont return any other response sentences or words other than the JSON object in markdown code.
                        """,
                    },
                        {
                            "type": "text",
                            "text": f"""
                                    Extract brand campaign data from all the information in the following content, with these columns: company_name, product_name, product_cost, product_description, nutritional_information (as a single no multilevel allowed nested object), and ingredients. If data is missing, use 'NA'. Only include data for a single brand. Ignore irrelevant links. Ensure all keys are in snake_case. Return the result as a JSON object in markdown code format. Be descriptive and include all relevant content.Be smart and make all adjustments to include it in the necessary columns so we can avoid unnecessary nA's
                                    """,
                        },
                        {
                            "type": "text",
                            "text": content,
                        },
                    ],
                }
            ],
        )

        extracted_data = response.choices[0].message.content.strip()
        print("Extracted data:", extracted_data)
        lines = extracted_data.splitlines()[1:-1]
        cleaned_data = '\n'.join(lines).strip()
        return cleaned_data

    except Exception as e:
        print(f"Error extracting brand data from content.txt: {e}")


def extract_product_data(api_key, identified_product=None, image_path=None):
    client = OpenAI(api_key=api_key)
    variation = None
    if identified_product is None:
        with open(image_path, "rb") as image_file:
            base64_im = base64.b64encode(image_file.read()).decode('utf-8')
        variation = [
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
                        "text": f"for the above image extract the following columns if you have information on this product(the exact same product in the image),so if you dont have any idea on this specific product please return the number 0 and nothing else. I dont want you to return any hallucinations,if you don't know the product or can't clearly see the product just return 0.If you arent able to get unhallucinated information on even one of the specified columns return 0 ",
                    },
                    {
                        "type": "text",
                        "text": f"EVEN IF ONE KEY HAS VALUE NA RETURN 0(the string 0 not in markdown code) ",
                    },
                    {
                        "type": "text",
                        "text": f"""company_name, product_name, product_cost, product_description,nutritional information and ingredients if information cannot be found for that field return NA,be smart and extract as much relevant information as possible return as a VALID json string in markdown code correctly formatted(ensure it is just key followed by a string, no arrays,nested arrays etc except for nutritional info which should have a nested json if there is any information else NA for the value field of nutritional info)
                              ensure product name is a safe file name format so i can use it directly in a file name
                              if you are unaware of the product, dont try and return information by parsing the image,just return 0
                              so even if you think one of the columns is na return 0,also keys always in snake case.
                              if you are returning 0 no need to give it in markdown,just the string 0 is fine
                              """,
                    },
                ],
            }
        ]
    elif image_path is None:
        variation = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"given this product {identified_product} extract the following columns if you have information on this product(the exact product not any variation of it), I dont want you to return any hallucinations,so if you dont have any idea on this specific product please return the number 0 and nothing else. I dont want you to return any hallucinations,if you don't know the product just return 0,If you arent able to get unhallucinated information on even one of the specified columns return 0",
                    },
                    {
                        "type": "text",
                        "text": f"""company_name, product_name, product_cost, product_description,nutritional information and ingredients if information cannot be found for that field return NA,be smart and extract as much relevant information as possible return as a VALID json string in markdown code correctly formatted(ensure it is just key followed by a string, no arrays,nested arrays etc except for nutritional info which should have a nested json if there is any information else NA for the value field of nutritional info)
                              ensure product name is a safe file name format so i can use it directly in a file name
                              if you are unaware of the product, dont try and return information by parsing the image,just return 0
                              so even if you think one of the columns is na return 0
                              if you are returning 0 no need to give it in markdown,just the string 0 is fine
                              """,
                    },
                ],
            }
        ]

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=variation,
    )
    extracted_data = response.choices[0].message.content.strip()
    print("Extracted data:", extracted_data)
    if extracted_data == "0":
        return ""
    else:
        lines = extracted_data.splitlines()[1:-1]
        cleaned_data = '\n'.join(lines).strip()
        return cleaned_data
