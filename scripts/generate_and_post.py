import os
import requests
import cloudinary
import cloudinary.uploader

# 1. Secrets
hf_token = os.getenv("HF_API_TOKEN")
instagram_token = os.getenv("META_ACCESS_TOKEN")
ig_business_id = os.getenv("META_BUSINESS_ID")

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
)

# 2. Genereer afbeelding met Hugging Face
prompt = "A futuristic architectural concept in a European city"
hf_resp = requests.post(
    "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2",
    headers={"Authorization": f"Bearer {hf_token}"},
    json={"inputs": prompt}
)

# 3. Check of het resultaat een geldige afbeelding is
content_type = hf_resp.headers.get("Content-Type", "")
if hf_resp.status_code != 200 or not content_type.startswith("image/"):
    print("❌ Hugging Face API gaf geen geldige afbeelding terug!")
    print("Status code:", hf_resp.status_code)
    print("Content-Type:", content_type)
    print("Response:", hf_resp.text)
    exit(1)

# 4. Sla afbeelding op
with open("output.png", "wb") as f:
    f.write(hf_resp.content)
print("✅ Afbeelding gegenereerd en opgeslagen")

# 5. Upload naar Cloudinary
try:
    up = cloudinary.uploader.upload("output.png", folder="daily_posts")
    image_url = up["secure_url"]
    print("✔️ Geüpload naar Cloudinary:", image_url)
except Exception as e:
    print("❌ Fout bij upload naar Cloudinary:", e)
    exit(1)

# 6. Post naar Instagram
media = requests.post(
    f"https://graph.facebook.com/v16.0/{ig_business_id}/media",
    data={"image_url": image_url, "caption": f"✨ {prompt}", "access_token": instagram_token}
).json()
print("📦 Media upload respons:", media)
if 'id' not in media:
    print("❌ Geen media-id:", media)
    exit(1)

publish = requests.post(
    f"https://graph.facebook.com/v23.0/{ig_business_id}/media_publish",
    data={"creation_id": media['id'], "access_token": instagram_token}
).json()
print("📤 Publicatie:", publish)
