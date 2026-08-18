import os
import random
import requests
import cloudinary
import cloudinary.uploader
import base64
import time
from io import BytesIO

# --- LOCATIE FUNCTIE TOEGEVOEGD ---
def get_location_id(city_name, access_token):
    url = "https://graph.facebook.com/v17.0/ig_location_search"
    params = {
        "q": city_name,
        "fields": "id,name",
        "access_token": access_token
    }
    resp = requests.get(url, params=params, timeout=30)
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

green_roof_phrase = ""
if random.random() < 0.4:
    green_roof_phrase = "green roofs, "

# 3. Concept Prompts
# Zelfde vijf inhoudelijke concepten als voordien, maar preciezer omschreven
# voor realistische architectuur en minder typische AI-fouten.
prompts = [
    (
        "Architectural photograph of a visionary {building_type} in {city}, designed as a plausible built project "
        "with clear structural logic, realistic spans, buildable façades and coherent circulation. "
        "The concept focuses on innovative sustainable architecture: {green_roof_phrase}integrated photovoltaic panels, "
        "visible but architecturally integrated water reuse, passive shading and climate-responsive design. "
        "Use {material1} and {material2} as the dominant materials, with realistic joints, thicknesses, weathering and construction details. "
        "The architecture must respond to the urban scale and character of {city}, without copying a known landmark. "
        "Include a believable public realm with correctly scaled people using the building naturally."
    ),
    (
        "Architectural photograph of a contemporary {building_type} in {city}, rooted in local history, craft and urban character "
        "without imitating a specific existing building. Translate traditional proportions, rhythms or spatial ideas into a new design. "
        "Combine {material1} with {material2} in a restrained, buildable way, with coherent façade depth, window placement and structural logic. "
        "The result should feel familiar to its context yet clearly contemporary and forward-looking. "
        "Show realistic human scale, entrances, ground-floor interaction and public space."
    ),
    (
        "Architectural photograph of a new {building_type} in {city} conceived primarily as a place for social interaction and community life. "
        "Organize the project around inviting plazas, sheltered thresholds, terraces and visible shared spaces that connect logically to entrances. "
        "Use {material1} and {material2} consistently, with realistic detailing and construction. "
        "Integrate planting as part of the spatial design rather than decorative green walls everywhere. "
        "People should gather, walk, sit and interact naturally at believable scale."
    ),
    (
        "Architectural photograph of a flexible and adaptable {building_type} in {city}. "
        "Express a rational structural grid, generous floor-to-floor heights, reusable spaces and a modular envelope that could realistically change over time. "
        "Use {material1} and {material2} with a clear hierarchy between structure, infill and openings. "
        "Avoid arbitrary futuristic shapes: innovation should come from adaptability, spatial quality and construction logic. "
        "Show an active building with realistic circulation, entrances and people."
    ),
    (
        "Architectural photograph of an experimental {building_type} in {city} where the form grows logically from programme, structure and public use. "
        "Create one strong architectural idea rather than multiple unrelated gestures. "
        "Use {material1} and {material2} with realistic thickness, connections, façade rhythm and structural support. "
        "A rooftop public space, stepped landscape or open amphitheatre may be integrated only if it is spatially and structurally plausible. "
        "Show people exploring and using the building naturally, with correct human scale."
    )
]

# 4. Post Counter
counter_file = "post_counter.txt"
try:
    with open(counter_file, "r") as f:
        post_counter = int(f.read().strip())
except FileNotFoundError:
    post_counter = 0

concept_idx = (post_counter // 3) % len(prompts)
prompt_template = prompts[concept_idx]
prompt = (
    prompt_template.format(
        city=city,
        building_type=building_type,
        material1=material1,
        material2=material2,
        green_roof_phrase=green_roof_phrase
    )
    + (
        " Professional architectural photography, eye-level or slightly elevated camera, 28–35 mm full-frame lens, "
        "straight verticals, natural perspective, physically plausible daylight at warm late-afternoon golden hour. "
        "Restrained contemporary color palette, realistic material texture, subtle imperfections, believable reflections and shadows. "
        "Editorial architecture magazine quality, photorealistic rather than illustrative. "
        "No impossible cantilevers, warped geometry, melted façades, duplicated building elements, random openings, floating objects, "
        "distorted people, extra limbs, illegible signage, fake text, excessive sci-fi styling or ornamental complexity."
    )
)

print(f"⚡️ Post count: {post_counter} | Concept index: {concept_idx} | Seed: {seed} | City: {city} | Building: {building_type} | Materials: {material1} + {material2}")

# 5. Generate Image
# Eerst vaste kwaliteitsmodellen. Als die tijdelijk niet beschikbaar zijn,
# zoeken we dynamisch naar een live Hugging Face text-to-image model.
def get_dynamic_hf_models(exclude_models=None, max_models=5):
    exclude_models = set(exclude_models or [])
    url = "https://huggingface.co/models-json"
    params = {
        "pipeline_tag": "text-to-image",
        "inference_provider": "hf-inference",
        "sort": "trending",
        "withCount": "true"
    }

    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        models = data.get("models", [])
        candidates = []

        for model in models:
            for provider in model.get("availableInferenceProviders", []):
                if (
                    provider.get("provider") == "hf-inference"
                    and provider.get("modelStatus") == "live"
                ):
                    model_id = provider.get("providerId")
                    if model_id and model_id not in exclude_models and model_id not in candidates:
                        candidates.append(model_id)

                    if len(candidates) >= max_models:
                        return candidates

        return candidates

    except Exception as e:
        print("⚠️ Fout bij dynamisch ophalen van HF-modellen:", e)
        return []


# De bestaande HF token blijft gebruikt worden. Hugging Face kiest automatisch
# een beschikbare Inference Provider voor het gekozen model.
def generate_image(prompt, seed, hf_token):
    if not hf_token:
        print("⚠️ Geen HF_API_TOKEN gevonden.")
        return None

    try:
        from huggingface_hub import InferenceClient
    except ImportError:
        print("❌ huggingface_hub ontbreekt. Voeg 'huggingface_hub' toe aan requirements.txt.")
        return None

    preferred_models = [
        "black-forest-labs/FLUX.1-Krea-dev",
        "black-forest-labs/FLUX.1-dev",
        "black-forest-labs/FLUX.1-schnell",
    ]

    client = InferenceClient(
        api_key=hf_token,
        provider="auto",
        timeout=180,
    )

    # 1. Eerst de vaste kwaliteitsmodellen proberen
    for model_id in preferred_models:
        print(f"🔄 Gebruik voorkeursmodel: {model_id}")
        try:
            image = client.text_to_image(
                prompt,
                model=model_id,
                seed=seed,
                width=1024,
                height=1024,
            )

            buffer = BytesIO()
            image.save(buffer, format="PNG")
            print(f"✅ Afbeelding ontvangen van {model_id}")
            return buffer.getvalue()

        except Exception as e:
            print(f"⚠️ Voorkeursmodel {model_id} mislukt of niet beschikbaar: {e}")

    # 2. Als alle voorkeursmodellen falen: dynamisch live HF-model proberen
    dynamic_models = get_dynamic_hf_models(
        exclude_models=preferred_models,
        max_models=5,
    )

    if dynamic_models:
        print(f"🔁 {len(dynamic_models)} dynamische HF-fallback(s) gevonden.")
    else:
        print("⚠️ Geen dynamische live HF-fallbacks gevonden.")

    for model_id in dynamic_models:
        print(f"🔄 Gebruik dynamische HF-fallback: {model_id}")
        try:
            image = client.text_to_image(
                prompt,
                model=model_id,
                seed=seed,
                width=1024,
                height=1024,
            )

            buffer = BytesIO()
            image.save(buffer, format="PNG")
            print(f"✅ Afbeelding ontvangen van dynamische fallback {model_id}")
            return buffer.getvalue()

        except Exception as e:
            print(f"⚠️ Dynamische fallback {model_id} mislukt: {e}")

    print("❌ Geen Hugging Face model kon een afbeelding genereren.")
    return None


image_content = generate_image(prompt, seed, hf_token)

# Fallback 1: Stability AI v2beta core
if image_content is None and stability_api_key:
    headers = {
      "Authorization": f"Bearer {stability_api_key}",
      "Accept": "application/json"
    }
    files = {
      "prompt": (None, prompt),
      "output_format": (None, "png")
    }
    try:
        response = requests.post("https://api.stability.ai/v2beta/stable-image/generate/core", headers=headers, files=files, timeout=120)
        if response.status_code == 200:
            image_b64 = response.json().get("image")
            if image_b64:
                image_content = base64.b64decode(image_b64)
    except requests.exceptions.RequestException as e:
        print("❌ Stability core netwerkfout:", e)

# Fallback 2: Stability AI SDXL via v2beta
if image_content is None and stability_api_key:
    headers = {
      "Authorization": f"Bearer {stability_api_key}",
      "Content-Type": "application/json",
      "Accept": "application/json"
    }
    payload = {
      "text_prompts": [{"text": prompt}],
      "cfg_scale": 7,
      "height": 1024,
      "width": 1024,
      "samples": 1,
      "steps": 30
    }
    try:
        response = requests.post("https://api.stability.ai/v2beta/stable-image/generate/sdxl", headers=headers, json=payload, timeout=120)
        if response.status_code == 200:
            image_content = base64.b64decode(response.json()["artifacts"][0]["base64"])
    except requests.exceptions.RequestException as e:
        print("❌ Stability SDXL netwerkfout:", e)

# Beveiligd wegschrijven
if not image_content:
    print("❌ Geen afbeelding gegenereerd na alle pogingen. Stop run.")
    raise SystemExit(1)

with open("output.png", "wb") as f:
    f.write(image_content)
print("✅ Image saved as output.png")

# 6. Upload naar Cloudinary
try:
    up = cloudinary.uploader.upload("output.png", folder="daily_posts")
    image_url = up["secure_url"]
    print("✔️ Uploaded successfully:", image_url)
except Exception as e:
    print("❌ Upload error:", e)
    raise SystemExit(1)

# 7. Caption bouwen
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

short_descriptions = [
    f"Exploring the blend of {material1} and {material2} in the heart of {city}.",
    f"Where innovation meets tradition: {building_type} designed for the future.",
    f"AI-powered vision for a new {building_type} in {city}, with sustainable touches."
]
cta_questions = [
    "How would you feel in this space? Drop your thoughts!",
    "What atmosphere does this evoke for you? Let us know below!",
    "Save for inspiration or share your opinion below!"
]
desc1 = random.choice(short_descriptions)
cta = random.choice(cta_questions)

hashtag_sets = [
    [
        "#AIinArchitecture", "#GenerativeDesign", "#ParametricDesign", "#DigitalArchitecture", "#AIDesign",
        "#ArchitectureLovers", "#Archilovers", "#ModernArchitecture", "#ArchitectureAndTechnology",
        "#SmartArchitecture", "#AlgorithmicDesign", "#FuturisticArchitecture", "#ArchDaily", "#Dezeen",
        "#urbaninnovation", "#futurecities", "#aiarchviz", "#architecturegram", "#cityvision", "#architecture_hunter", city_hashtag
    ],
    [
        "#DesignWithAI", "#MachineLearningDesign", "#ArchitecturalInnovation", "#NextGenDesign", "#TechInArchitecture",
        "#ArchitectsOfInstagram", "#ContemporaryArchitecture", "#ArchitectureCommunity", "#InteriorArchitecture",
        "#CreativeArchitecture", "#ArchitectureVisualization", "#DesignBoom", "#FuturisticArchitecture", "#urbaninnovation",
        "#aiarchitecture", "#AIinArchitecture", "#AlgorithmicDesign", "#ModernArchitecture", "#ArchDaily", city_hashtag
    ],
    [
        "#AIDesign", "#SmartArchitecture", "#ParametricArchitecture", "#GenerativeArt", "#ArchitectureView",
        "#ArchitectureModel", "#UrbanArchitecture", "#ArchitectureDetail", "#ArchDaily", "#Dezeen",
        "#AIDesignCommunity", "#ArchitectureInnovation", "#AIinArchitecture", "#futurecities", "#DesignBoom",
        "#AlgorithmicDesign", "#architecturelovers", "#architecture_hunter", "#cityvision", city_hashtag
    ],
    [
        "#architecturelovers", "#aiart", "#conceptarchitecture", "#futureofarchitecture", "#cityscape",
        "#europeancities", "#archdaily", "#innoarchdaily", "#futuristicarchitecture", "#cityvision", "#dreambuildings",
        "#stedenbouw", "#urbansketch", "#aiarchitecture", "#architectuur", "#designlovers", "#AlgorithmicDesign",
        "#ModernArchitecture", "#AIinArchitecture", city_hashtag, "#artificialintelligence"
    ]
]
hashtag_list = hashtag_sets[post_counter % len(hashtag_sets)]

caption = (
    f"✨ {series_title}\n"
    f"{desc1}\n\n"
    f"{cta}\n\n"
    f"{' '.join(hashtag_list)}"
)

# 8. Post naar Instagram (zelfde API-versies; enkel wachten tot Meta klaar is)
def wait_until_media_ready(container_id, access_token, max_attempts=12, wait_seconds=5):
    status_url = f"https://graph.facebook.com/v23.0/{container_id}"

    for attempt in range(max_attempts):
        try:
            response = requests.get(
                status_url,
                params={
                    "fields": "status_code",
                    "access_token": access_token
                },
                timeout=30
            )
            data = response.json()
            status = data.get("status_code")

            print(f"⏳ Media verwerking ({attempt + 1}/{max_attempts}): {status}")

            if status == "FINISHED":
                print("✅ Media klaar voor publicatie.")
                return True

            if status in ("ERROR", "EXPIRED"):
                print("❌ Media processing mislukt:", data)
                return False

        except requests.exceptions.RequestException as e:
            print("⚠️ Fout tijdens statuscontrole:", e)

        time.sleep(wait_seconds)

    print("❌ Media werd niet tijdig klaar voor publicatie.")
    return False

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
    data=media_data,
    timeout=60
).json()
print("📦 Media upload response:", media)
if 'id' not in media:
    print("❌ No media id received – abort:", media)
    raise SystemExit(1)

media_id = media["id"]

if not wait_until_media_ready(media_id, instagram_token):
    print("❌ Publicatie afgebroken omdat media niet klaar is.")
    raise SystemExit(1)

publish = requests.post(
    f"https://graph.facebook.com/v23.0/{ig_business_id}/media_publish",
    data={"creation_id": media_id, "access_token": instagram_token},
    timeout=60
).json()
print("📤 Publish result:", publish)

if "id" not in publish:
    print("❌ Instagram-publicatie mislukt:", publish)
    raise SystemExit(1)

# 9. Counter bijwerken
with open(counter_file, "w") as f:
    f.write(str(post_counter + 1))
print("✅ Counter updated. Post ready!")
