import os
import requests

# 1. Genereer AI-afbeelding via Hugging Face
prompt = "modern architecture innovation"
hf_url = "https://api-inference.huggingface.co/models/stable-diffusion-v1-5"
hf_headers = {"Authorization": f"Bearer {os.getenv('HF_API_TOKEN')}"}
response = requests.post(hf_url, headers=hf_headers, json={"inputs": prompt})
with open('output.png', 'wb') as f:
    f.write(response.content)

# 2. Maak caption
caption = f"Architectuur innovatie van de dag: {prompt}. #architectuur #innovation"

# 3. Post naar Instagram
business_id = os.getenv('INSTA_BUSINESS_ID')
access_token = os.getenv('INSTA_ACCESS_TOKEN')
# Media-object aanmaken
data = {
    'image_url': 'https://jouwdomein.nl/output.png',
    'caption': caption,
    'access_token': access_token
}
media_resp = requests.post(
    f"https://graph.facebook.com/v16.0/{business_id}/media", data=data
).json()

# Publiceren
publish_resp = requests.post(
    f"https://graph.facebook.com/v16.0/{business_id}/media_publish",
    data={'creation_id': media_resp['id'], 'access_token': access_token}
).json()
print('Gepost:', publish_resp)
