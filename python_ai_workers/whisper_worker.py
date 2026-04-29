import os
import whisper
import tempfile
import warnings
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse

# Αγνοούμε κάποια σπαστικά warnings της Python για να βλέπεις καθαρά τα logs
warnings.filterwarnings("ignore")

app = FastAPI(title="Local Whisper API", version="1.0")

print("🚀 [WHISPER] Loading AI Model into VRAM (CUDA)...")
# Φορτώνουμε το μοντέλο στη GPU. 
# Αν δεν έχεις GPU ή δεν έχουν μπει σωστά οι CUDA drivers, θα το βάλει αυτόματα στη CPU.
model = whisper.load_model("base")
print("✅ [WHISPER] Model loaded! Ready for requests.")

@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    print(f"📥 [API] Received audio file: {file.filename}")
    
    # 1. Φτιάχνουμε το "άδειο ποτήρι" (temp file) για να μαζέψουμε τις σταγόνες (bytes)
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            # Ρουφάμε τα bytes από το δίκτυο και τα γράφουμε στον δίσκο
            temp_audio.write(await file.read())
            temp_audio_path = temp_audio.name
            
        # 2. Δίνουμε το έτοιμο "ποτήρι" στον Σεφ (Whisper) να κάνει τη μετάφραση
        print("🧠 [WHISPER] Transcribing audio...")
        result = model.transcribe(temp_audio_path)
        
        # 3. Πετάμε το "ποτήρι" (διαγραφή αρχείου) για να μη γεμίσει σκουπίδια ο δίσκος μας
        os.remove(temp_audio_path)
        
        print(f"📝 [WHISPER] Transcription Success: {result['text'].strip()}")
        
        # 4. Στέλνουμε το αποτέλεσμα πίσω σε μορφή JSON (κοινή γλώσσα)
        return JSONResponse(content={"text": result["text"].strip(), "status": "success"})
        
    except Exception as e:
        print(f"❌ [ERROR] Transcription failed: {e}")
        return JSONResponse(content={"error": str(e), "status": "failed"}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    # Ξεκινάμε τον Σερβιτόρο στη διεύθυνση http://localhost:8000
    print("🌐 Starting API server on port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)