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

# 3. Concept Prompts
prompts = [
    "Design a visionary {building_type} in {city} that showcases innovative sustainable architecture. The building features green roofs, extensive use of {material1} and {material2}, integrated solar panels, and visible water recycling systems. The design feels rooted in the city’s context, and is bustling with people interacting during golden hour.",
    "Create a futuristic {building_type} in {city}, inspired by local history, art, or iconic architectural motifs. Blend traditional {material1} with cutting-edge {material2}, resulting in a building that feels both familiar and forward-thinking. Present the scene at golden hour, with people engaging in and around the building.",
    "Generate a concept {building_type} in {city} designed for social interaction and community gathering. Incorporate inviting plazas, open terraces, and vibrant public spaces. The architecture features a mix of {material1} and {material2}, with greenery woven throughout. Lively crowds of people interact during golden hour.",
    "Imagine a flexible mixed-use {building_type} in {city}, capable of adapting to changing community needs. The structure combines modular design, multi-purpose spaces, and materials like {material1} and {material2}. The building is filled with activity and interaction, shown at golden hour.",
    "Design an experimental {building_type} in {city} where the building’s unique form is driven by its function. Use unexpected combinations of {material1} and {material2}, and integrate features like rooftop parks or open amphitheaters. The image captures people exploring the innovative spaces at golden hour."
]

prompt_template = random.choice(prompts)
prompt = prompt_template.format(
    city=city,
    building_type=building_type,
    material1=material1,
    material2=material2
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
print("⚡️ Seed:", seed, "| City:", city, "| Building:", building_type, "| Materials:", material1, "+", material2)

content_type = hf_resp.headers.get("Content-Type", "")
if hf_resp.status_code != 200 or not content_type.startswith("image/"):
    print("❌ No image returned — model might be unavailable?")
    print("Status:", hf_resp.status_code, "Content-Type:", content_type)
    print("Response:", hf_resp.text)
    exit(1)

# 5. Save image
with open("output.png", "wb") as f:
    f.write(hf_resp.content)
print("✅ Image saved as output.png")

# 6. Upload to Cloudinary
try:
    up = cloudinary.uploader.upload("output.png", folder="daily_posts")
    image_url = up["secure_url"]
    print("✔️ Uploaded successfully:", image_url)
except Exception as e:
    print("❌ Upload error:", e)
    exit(1)

# 7. Hashtags
hashtags = [
    "#architecturelovers", "#aiart", "#conceptarchitecture", "#futureofarchitecture",
    "#cityscape", "#europeancities", "#archdaily", "#innoarchdaily", "#futuristicarchitecture",
    "#cityvision", "#dreambuildings", "#stedenbouw", "#urbansketch", "#aiarchitecture",
    "#architectuur", "#designlovers", city_hashtag, "#artificialintelligence"
]
caption = (
    f"✨ {city}: {building_type.capitalize()} in {material1} and {material2}. Futuristic architecture meets real city vibes.\n\n"
    f"{' '.join(hashtags)}"
)

# 8. Post to Instagram
media = requests.post(
    f"https://graph.facebook.com/v16.0/{ig_business_id}/media",
    data={"image_url": image_url, "caption": caption, "access_token": instagram_token}
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
