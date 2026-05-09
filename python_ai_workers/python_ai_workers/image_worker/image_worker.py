import torch
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from diffusers import StableDiffusionPipeline
import uuid
import os
import warnings

# Κρύβουμε τα σπαστικά warnings
warnings.filterwarnings("ignore")

app = FastAPI(title="Local Image Gen API (Stable Diffusion)", version="1.0")

# Φτιάχνουμε τη βιτρίνα
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

print("🚀 [STABLE-DIFFUSION] Loading model to RAM (CPU Mode)...")
pipe = StableDiffusionPipeline.from_pretrained("runwayml/stable-diffusion-v1-5")

# SOS: Δολοφονούμε τον Safety Checker για να μη βγάζει μαύρες εικόνες!
pipe.safety_checker = None
pipe.requires_safety_checker = False

print("✅ [STABLE-DIFFUSION] Model ready! Waiting for requests...")

class ImageRequest(BaseModel):
    prompt: str

@app.post("/generate-image")
def generate_image(req: ImageRequest):
    print(f"🎨 [API] Received prompt: {req.prompt}")
    try:
        print("⏳ Ζωγραφίζει... υπομονή (CPU Mode 12 steps)...")
        # Βάζουμε 12 βήματα και 256x256 για να μην πάρει ώρες, αλλά να βγει καθαρό
        image = pipe(
            req.prompt,
            num_inference_steps=50, 
            height=512,
            width=512,
            guidance_scale=7.5
        ).images[0]
        
        filename = f"cover_{uuid.uuid4().hex[:8]}.png"
        filepath = os.path.join("static", filename)
        image.save(filepath)
        
        image_url = f"http://localhost:8001/static/{filename}"
        print(f"✅ [SUCCESS] Image generated at: {image_url}")
        return {"image_url": image_url, "status": "success"}
    except Exception as e:
        print(f"❌ [ERROR] Image generation failed: {e}")
        return {"error": str(e), "status": "failed"}