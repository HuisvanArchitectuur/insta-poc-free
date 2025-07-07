import os
import random
import requests
import cloudinary
import cloudinary.uploader
import base64
import json

# --- LOCATIE FUNCTIE ---
def get_location_id(city_name, access_token):
    url = "https://graph.facebook.com/v17.0/ig_location_search"
    params = {
        "q": city_name,
        "fields": "id,name",
        "access_token": access_token
    }
    resp = requests.get(url, params=params)
    if resp.status_code == 200:
        data = resp.json()
        if 'data' in data and data['data']:
            return data['data'][0]['id']
    print(f"⚠️ Geen locatie-id gevonden voor: {city_name}")
    return None

# 1. Secrets
hf_token = os.getenv("HF_API_TOKEN")
stability_api_key = os.getenv("STABILITY_API_KEY")
instagram_token = os.getenv("META_ACCESS_TOKEN")
ig_business_id = os.getenv("META_BUSINESS_ID")

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
)

# 2. Random seed en variabelen
seed = random.randint(0, 99999999)
cities = [
    ("Paris", "#parisarchitecture"),
    ("Barcelona", "#barcelonaarchitecture"),
    ("Amsterdam", "#amsterdamarchitecture"),
    ("Vienna", "#viennaarchitecture"),
    ("Prague", "#praguearchitecture"),
    ("Berlin", "#berlinarchitecture"),
    ("Milan", "#milanarchitecture"),
]
building_types = ["library", "museum", "market hall", "school", "housing", "theater", "sports center"]
materials1 = ["timber", "brick", "glass", "corten steel", "natural stone", "recycled concrete"]
materials2 = ["glass", "steel", "green walls", "polished concrete", "ceramics"]

city, city_hashtag = random.choice(cities)
building_type = random.choice(building_types)
material1, material2 = random.sample(materials1 + materials2, 2)
green_roof_phrase = "green roofs, " if random.random() < 0.4 else ""

# 3. Prompts
prompts = [
    "Design a visionary {building_type} in {city} that showcases innovative sustainable architecture. The building features {green_roof_phrase}extensive use of {material1} and {material2}, integrated solar panels, and visible water recycling systems. The design feels rooted in the city’s context, and is bustling with people interacting during golden hour.",
    "Create a futuristic {building_type} in {city}, inspired by local history, art, or iconic architectural motifs. Blend traditional {material1} with cutting-edge {material2}, resulting in a building that feels both familiar and forward-thinking. Present the scene at golden hour, with people engaging in and around the building.",
    "Generate a concept {building_type} in {city} designed for social interaction and community gathering. Incorporate inviting plazas, open terraces, and vibrant public spaces. The architecture features a mix of {material1} and {material2}, with greenery woven throughout. Lively crowds of people interact during golden hour.",
    "Imagine a flexible mixed-use {building_type} in {city}, capable of adapting to changing community needs. The structure combines modular design, multi-purpose spaces, and materials like {material1} and {material2}. The building is filled with activity and interaction, shown at golden hour.",
    "Design an experimental {building_type} in {city} where the building’s unique form is driven by its function. Use unexpected combinations of {material1} and {material2}, and integrate features like rooftop parks or open amphitheaters. The image captures people exploring the innovative spaces at golden hour."
]

# 4. Post counter
counter_file = "post_counter.txt"
try:
    with open(counter_file, "r") as f:
        post_counter = int(f.read().strip())
except FileNotFoundError:
    post_counter = 0

concept_idx = (post_counter // 3) % len(prompts)
prompt = prompts[concept_idx].format(
    city=city,
    building_type=building_type,
    material1=material1,
    material2=material2,
    green_roof_phrase=green_roof_phrase
) + " Neutral color palette, architectural photography, editorial style, ultra realistic, 4K, matte finish, photo-realistic, cinematic, architectural magazine, detailed lighting."

print(f"⚡️ Post count: {post_counter} | Concept index: {concept_idx} | Seed: {seed} | City: {city} | Building: {building_type} | Materials: {material1} + {material2}")

# 5. Hugging Face Endpoints
HF_ENDPOINTS = [
    "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-3.5-large-turbo",
    "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-3.5-large",
    "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-dev",
    "https://api-inference.huggingface.co/models/SG161222/Realistic_Vision_V6.0_B1_noVAE"
]

def generate_image(prompt, seed, hf_token, endpoints):
    headers = {"Authorization": f"Bearer {hf_token}"}
    data = {"inputs": prompt, "parameters": {"seed": seed}}
    for endpoint in endpoints:
        print(f"🔄 Probeer endpoint: {endpoint}")
        resp = requests.post(endpoint, headers=headers, json=data)
        content_type = resp.headers.get("Content-Type", "")
        if resp.status_code == 200 and content_type.startswith("image/"):
            print(f"✅ Afbeelding ontvangen van {endpoint}")
            return resp.content
        else:
            print(f"❌ Fout bij {endpoint}: Status {resp.status_code}, Content-Type: {content_type}")
            print("Response:", resp.text)
    return None

image_content = generate_image(prompt, seed, hf_token, HF_ENDPOINTS)

# 6. Fallback 1: Stability v2beta
if image_content is None:
    print("🔁 Fallback naar Stability v2beta...")
    if not stability_api_key:
        print("❌ STABILITY_API_KEY ontbreekt.")
        exit(1)

    stability_url = "https://api.stability.ai/v2beta/stable-image/generate/core"
    headers = {
        "Authorization": f"Bearer {stability_api_key}"
    }
    files = {
        "prompt": (None, prompt),
        "output_format": (None, "png")
    }

    response = requests.post(stability_url, headers=headers, files=files)
    if response.status_code == 200:
        result = response.json()
        image_b64 = result["image"]
        image_content = base64.b64decode(image_b64)
        print("✅ Afbeelding gegenereerd met Stability v2beta")
    else:
        print("❌ Fallback 1 faalde:", response.status_code, response.text)

# 7. Fallback 2: Stability SDXL v1
if image_content is None:
    print("🔁 Fallback naar Stability v1 SDXL...")
    stability_url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-beta-v2-2-2/text-to-image"
    headers = {
        "Authorization": f"Bearer {stability_api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "text_prompts": [{"text": prompt}],
        "cfg_scale": 7,
        "height": 512,
        "width": 768,
        "samples": 1,
        "steps": 30
    }

    response = requests.post(stability_url, headers=headers, json=payload)
    if response.status_code == 200:
        result = response.json()
        image_b64 = result["artifacts"][0]["base64"]
        image_content = base64.b64decode(image_b64)
        print("✅ Afbeelding gegenereerd met Stability SDXL")
    else:
        print("❌ Fallback 2 faalde ook:", response.status_code, response.text)
        exit(1)

# 8. Opslaan
with open("output.png", "wb") as f:
    f.write(image_content)
print("✅ Image saved as output.png")

# 9. Upload naar Cloudinary
try:
    up = cloudinary.uploader.upload("output.png", folder="daily_posts")
    image_url = up["secure_url"]
    print("✔️ Uploaded successfully:", image_url)
except Exception as e:
    print("❌ Upload error:", e)
    exit(1)

# 10. Caption
series_titles = [
    "FUTURISTIC {building_type} X {city}",
    "CONTEXTUAL DESIGN X {city}",
    "REIMAGINED SPACES X {city}",
    "URBAN VISION X {city}",
    "HISTORIC FUSION X {city}"
]
series_idx = (post_counter // 3) % len(series_titles)
series_title = series_titles[series_idx].format(
    building_type=building_type.upper(),
    city=city.upper()
)
desc = f"Exploring the blend of {material1} and {material2} in the heart of {city}."
cta = "What atmosphere does this evoke for you? Let us know below!"

hashtags = f"#architecture #aiarchitecture #conceptdesign {city_hashtag} #aiart #archdaily"

caption = f"✨ {series_title}\n{desc}\n\n{cta}\n\n{hashtags}"

# 11. Instagram Posting
location_id = get_location_id(city, instagram_token)
media_data = {
    "image_url": image_url,
    "caption": caption,
    "access_token": instagram_token
}
if location_id:
    media_data["location_id"] = location_id

media = requests.post(
    f"https://graph.facebook.com/v16.0/{ig_business_id}/media",
    data=media_data
).json()
print("📦 Media upload response:", media)
if 'id' not in media:
    print("❌ No media id received – abort:", media)
    exit(1)

publish = requests.post(
    f"https://graph.facebook.com/v23.0/{ig_business_id}/media_publish",
    data={"creation_id": media['id'], "access_token": instagram_token}
).json()
print("📤 Publish result:", publish)

# 12. Counter bijwerken
with open(counter_file, "w") as f:
    f.write(str(post_counter + 1))
