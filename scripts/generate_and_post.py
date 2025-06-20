import os, requests, cloudinary, cloudinary.uploader

# Secrets
hf_token = os.getenv("HF_API_TOKEN")
instagram_token = os.getenv("META_ACCESS_TOKEN")
ig_business_id = os.getenv("META_BUSINESS_ID")

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
)

# 1. Genereer afbeelding
prompt = "A futuristic architectural concept in a European city"
hf_resp = requests.post(
    "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2",
    headers={"Authorization": f"Bearer {hf_token}"},
    json={"inputs": prompt}
)
with open("output.png","wb") as f:
    f.write(hf_resp.content)
print("✅ Afbeelding gegenereerd")

# 2. Upload naar Cloudinary
up = cloudinary.uploader.upload("output.png", folder="daily_posts")
image_url = up["secure_url"]
print("✔️ Geüpload naar Cloudinary:", image_url)

# 3. Post naar Instagram
media = requests.post(
    f"https://graph.facebook.com/v16.0/{ig_business_id}/media",
    data={"image_url": image_url, "caption": f"✨ {prompt}", "access_token": instagram_token}
).json()
print("📦 Media upload respons:", media)
if 'id' not in media:
    print("❌ Geen media-id:", media); exit(1)

publish = requests.post(
    f"https://graph.facebook.com/v23.0/{ig_business_id}/media_publish",
    data={"creation_id": media['id'], "access_token": instagram_token}
).json()
print("📤 Publicatie:", publish)
