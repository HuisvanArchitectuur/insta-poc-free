import os
import requests

# 1. Ophalen van secrets
access_token = os.getenv('META_ACCESS_TOKEN')
business_id = os.getenv('INSTA_BUSINESS_ID')
hf_token = os.getenv('HF_API_TOKEN')

# 2. Genereer een afbeelding met Hugging Face
prompt = "A futuristic architectural concept in a European city"
headers = {
    "Authorization": f"Bearer {hf_token}"
}
response = requests.post(
    "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2",
    headers=headers,
    json={"inputs": prompt}
)

# 3. Sla afbeelding lokaal op
image_path = "output.png"
with open(image_path, "wb") as f:
    f.write(response.content)

print("✅ Afbeelding gegenereerd en opgeslagen als output.png")

# 4. Upload afbeelding naar een externe host (dit voorbeeld gebruikt een placeholder)
# In een echte situatie heb je een upload-URL nodig (bv. S3, ImgBB, Cloudinary...)
image_url = "https://via.placeholder.com/600x400.png?text=Demo+Architectuur"  # ← Vervang dit!

# 5. Maak Instagram-post (stap 1: media uploaden)
media_endpoint = f"https://graph.facebook.com/v16.0/{business_id}/media"
media_payload = {
    "image_url": image_url,
    "caption": f"✨ Dagelijkse inspiratie: {prompt}",
    "access_token": access_token
}
media_resp = requests.post(media_endpoint, data=media_payload).json()
print("📦 Antwoord van media upload:", media_resp)

# 6. Foutafhandeling
if 'id' not in media_resp:
    print("❌ Fout bij aanmaken media object: geen 'id' ontvangen")
    exit(1)

# 7. Publiceer post (stap 2)
publish_endpoint = f"https://graph.facebook.com/v16.0/{business_id}/media_publish"
publish_payload = {
    "creation_id": media_resp['id'],
    "access_token": access_token
}
publish_resp = requests.post(publish_endpoint, data=publish_payload).json()
print("📤 Publicatie resultaat:", publish_resp)
