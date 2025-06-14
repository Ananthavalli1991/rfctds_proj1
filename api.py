from fastapi import FastAPI
from pydantic import BaseModel
import faiss
import numpy as np
import json
import os
from openai import OpenAI
from dotenv import load_dotenv
from typing import Optional
import uvicorn
from PIL import Image
import pytesseract
import base64
import io

# ✅ Load environment variables
load_dotenv()

# ✅ Setup OpenAI client with AIPROXY or actual base URL
client = OpenAI(
    api_key=os.getenv("AIPROXY_TOKEN"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://aiproxy.sanand.workers.dev/openai/v1")  # fallback if not set
)

# ✅ Init FastAPI app
app = FastAPI()

# ✅ Tesseract path (for Windows)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# ✅ Load FAISS index and metadata
index = faiss.read_index(r"C:\Users\DELL\data\faiss.index")
with open(r"C:\Users\DELL\data\meta.json", "r", encoding="utf-8") as f:
    documents = json.load(f)

# ✅ Model names
EMBED_MODEL = "text-embedding-3-small"  # ✅ correct for AIPROXY
GPT_MODEL = "gpt-4o-mini"               # ✅ correct for AIPROXY

# ✅ Request schema
class QueryRequest(BaseModel):
    question: str
    image: Optional[str] = None  # base64-encoded image (optional)

@app.post("/api/")
async def rag_api(query: QueryRequest):
    question = query.question.strip()

    # 🔍 Optional OCR from base64 image
    if query.image:
        try:
            print("📷 Image received, extracting text...")
            image_bytes = base64.b64decode(query.image)
            image = Image.open(io.BytesIO(image_bytes))
            image = image.convert("L")  # grayscale
            image = image.resize((image.width * 2, image.height * 2))  # upscale

            ocr_text = pytesseract.image_to_string(image)
            print("🔍 OCR text:", ocr_text.strip())

            question += " " + ocr_text.strip()
        except Exception as e:
            print("❌ OCR failed:", e)

    # 🔗 Step 1: Embed the question
    try:
        response = client.embeddings.create(
            input=[question],
            model=EMBED_MODEL
        )
        print("✅ Embedding created")
        query_embedding = np.array(response.data[0].embedding, dtype="float32").reshape(1, -1)
    except Exception as e:
        print("❌ Embedding failed:", e)
        return {"error": f"Embedding failed: {str(e)}"}

    # 🔍 Step 2: Search FAISS index
    _, indices = index.search(query_embedding, k=5)
    top_docs = [documents[i] for i in indices[0]]

    # 📚 Step 3: Combine context
    context = "\n\n".join(doc["content"] for doc in top_docs)

    # 🧠 Step 4: Generate answer
    try:
        messages = [
            {"role": "system", "content": "You are a helpful TDS assistant. Use only the context below to answer."},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
        ]
        completion = client.chat.completions.create(
            model=GPT_MODEL,
            messages=messages
        )
        answer = completion.choices[0].message.content.strip()
    except Exception as e:
        print("❌ Chat generation failed:", e)
        return {"error": f"Chat completion failed: {str(e)}"}

    # 🔗 Step 5: Extract source links
    links = [
        {"url": doc.get("url"), "text": doc.get("title")}
        for doc in top_docs if doc.get("url")
    ]

    return {
        "answer": answer,
        "ocr_text": ocr_text.strip(), 
        "links": links
    }

# ✅ Run locally
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
