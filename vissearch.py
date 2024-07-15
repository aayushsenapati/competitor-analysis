import json
import requests


def extract_names(data):
    """Extract names from the specified path and append them to a string"""
    names = []
    if "tags" in data and data["tags"]:
        first_tag = data["tags"][0]
        if "actions" in first_tag and first_tag["actions"]:
            first_action = first_tag["actions"][0]
            if "data" in first_action and "value" in first_action["data"]:
                for value_item in first_action["data"]["value"]:
                    if "name" in value_item:
                        names.append(value_item["name"])
    return " ".join(names)

def vistonames(imagePath,SUBSCRIPTION_KEY,BASE_URI):
    HEADERS = {'Ocp-Apim-Subscription-Key': SUBSCRIPTION_KEY}
    file = {'image' : ('myfile', open(imagePath, 'rb'))}
    response = requests.post(BASE_URI, headers=HEADERS, files=file)
    response.raise_for_status()
    combstr=extract_names(response.json())
    return combstr