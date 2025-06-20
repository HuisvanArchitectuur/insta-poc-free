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

# 2. Genereer afbeelding
prompt = "A futuristic architectural concept in a European city"
hf_resp = requests.post(
    "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-3.5-large-turbo",
    headers={"Authorization": f"Bearer {hf_token}"},
    json={"inputs": prompt}
)

# 3. Validatie check
content_type = hf_resp.headers.get("Content-Type", "")
if hf_resp.status_code != 200 or not content_type.startswith("image/"):
    print("❌ API gaf geen afbeelding — mogelijk model onbeschikbaar?")
    print("Status:", hf_resp.status_code, "Content-Type:", content_type)
    print("Response:", hf_resp.text)
    exit(1)

# 4. Opslaan
with open("output.png", "wb") as f:
    f.write(hf_resp.content)
print("✅ Afbeelding opgeslagen als output.png")

# 5. Upload naar Cloudinary
try:
    up = cloudinary.uploader.upload("output.png", folder="daily_posts")
    image_url = up["secure_url"]
    print("✔️ Upload succesvol:", image_url)
except Exception as e:
    print("❌ Fout tijdens upload:", e)
    exit(1)

# 6. Publiceer op Instagram
media = requests.post(
    f"https://graph.facebook.com/v16.0/{ig_business_id}/media",
    data={"image_url": image_url, "caption": f"✨ {prompt}", "access_token": instagram_token}
).json()
print("📦 Media upload response:", media)
if 'id' not in media:
    print("❌ Geen media-id ontvangen – stop hier:", media)
    exit(1)

publish = requests.post(
    f"https://graph.facebook.com/v23.0/{ig_business_id}/media_publish",
    data={"creation_id": media['id'], "access_token": instagram_token}
).json()
print("📤 Publicatieresultaat:", publish)
