import os
import random
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

# 2. Random seed en stad
seed = random.randint(0, 99999999)
cities = [
    ("Paris", "#parisarchitecture"),
    ("Barcelona", "#barcelonaarchitecture"),
    ("Amsterdam", "#amsterdamarchitecture"),
    ("Vienna", "#viennaarchitecture"),
    ("Prague", "#praguearchitecture"),
]
city, city_hashtag = random.choice(cities)

# 3. Prompt
prompt = (
    f"Generate a highly aesthetic, futuristic concept building seamlessly integrated into a famous European cityscape "
    f"(such as Paris, Barcelona, Amsterdam, Vienna, or Prague). The building should blend innovative architecture with "
    f"recognizable urban elements, appealing to both architecture lovers and the general public. Focus on elegant forms, "
    f"natural materials, and vibrant colors. The image should look like a professional photograph, shot during golden hour, "
    f"with people interacting in and around the building, creating a lively, inviting atmosphere. Strong composition, realistic lighting, "
    f"and a touch of dreaminess. Keep the design plausible and inspirational, avoiding surrealism. The building must stand out but also "
    f"respect the context of the city. (city: {city})"
)

# 4. Genereer afbeelding
hf_resp = requests.post(
    "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-3.5-large-turbo",
    headers={"Authorization": f"Bearer {hf_token}"},
    json={
        "inputs": prompt,
        "parameters": {"seed": seed}
    }
)
print("⚡️ Gebruikte seed:", seed, "| Stad:", city)

content_type = hf_resp.headers.get("Content-Type", "")
if hf_resp.status_code != 200 or not content_type.startswith("image/"):
    print("❌ API gaf geen afbeelding — mogelijk model onbeschikbaar?")
    print("Status:", hf_resp.status_code, "Content-Type:", content_type)
    print("Response:", hf_resp.text)
    exit(1)

# 5. Opslaan
with open("output.png", "wb") as f:
    f.write(hf_resp.content)
print("✅ Afbeelding opgeslagen als output.png")

# 6. Upload naar Cloudinary
try:
    up = cloudinary.uploader.upload("output.png", folder="daily_posts")
    image_url = up["secure_url"]
    print("✔️ Upload succesvol:", image_url)
except Exception as e:
    print("❌ Fout tijdens upload:", e)
    exit(1)

# 7. Hashtags
hashtags = [
    "#architecturelovers", "#aiart", "#conceptarchitecture", "#futureofarchitecture",
    "#cityscape", "#europeancities", "#archdaily", "#innoarchdaily", "#futuristicarchitecture",
    "#cityvision", "#dreambuildings", "#stedenbouw", "#urbansketch", "#aiarchitecture",
    "#architectuur", "#designlovers", city_hashtag, "#artificialintelligence"
]
caption = (
    f"✨ {city}: futuristic architecture meets real city vibes.\n\n"
    f"{' '.join(hashtags)}"
)

# 8. Post naar Instagram
media = requests.post(
    f"https://graph.facebook.com/v16.0/{ig_business_id}/media",
    data={"image_url": image_url, "caption": caption, "access_token": instagram_token}
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
