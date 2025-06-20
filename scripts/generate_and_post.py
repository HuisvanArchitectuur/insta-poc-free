import os, requests, pyimgur

# 1. Secrets
hf_token = os.getenv("HF_API_TOKEN")
CLIENT_ID = os.getenv("IMGUR_CLIENT_ID")
CLIENT_SECRET = os.getenv("IMGUR_CLIENT_SECRET")
instagram_token = os.getenv("META_ACCESS_TOKEN")
ig_business_id = os.getenv("META_BUSINESS_ID")

# 2. Genereer afbeelding
prompt = "A futuristic architectural concept in a European city"
hf_resp = requests.post(
    "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2",
    headers={"Authorization": f"Bearer {hf_token}"},
    json={"inputs": prompt}
)
with open("output.png","wb") as f:
    f.write(hf_resp.content)
print("✅ Image gegenereerd en opgeslagen")

# 3. Upload naar Imgur
im = pyimgur.Imgur(CLIENT_ID, CLIENT_SECRET)
uploaded = im.upload_image("output.png", title=prompt)
image_url = uploaded.link
print("✔️ Geüpload naar Imgur:", image_url)

# 4. Post naar Instagram
media = requests.post(
    f"https://graph.facebook.com/v16.0/{ig_business_id}/media",
    data={"image_url": image_url, "caption": f"✨ {prompt}", "access_token": instagram_token}
).json()
print("📦 Media upload respons:", media)
if 'id' not in media:
    print("❌ Geen media-id ontvangen:", media); exit(1)
publish = requests.post(
    f"https://graph.facebook.com/v23.0/{ig_business_id}/media_publish",
    data={"creation_id": media['id'], "access_token": instagram_token}
).json()
print("📤 Publicatie:", publish)
