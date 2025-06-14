# TDS Virtual TA 🧠

A FastAPI-based Virtual Teaching Assistant for the TDS (Tools in Data Science) course offered by IITM.  
This API answers student questions using course content and Discourse posts, and can even read screenshots using OCR.

---

## 🌐 Live API

> 🔗 **POST** [`https://tds-virtual-ta.onrender.com/api/`](https://tds-virtual-ta.onrender.com/api/)

---

## 📦 Features

- 📚 Answers based on:
  - TDS Jan 2025 course content 
  - TDS Discourse posts (Jan 1 – Apr 14, 2025)
- 🔍 Semantic search using FAISS
- 📷 Image OCR from base64 screenshots (e.g., GA questions)
- ⚡ Responds in under 30 seconds
- 🔗 Returns relevant source links (Discourse + course pages)

---

## 🧪 Example Request

```bash
curl -X POST https://tds-virtual-ta.onrender.com/api/ \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Is GitHub Copilot used in the TDS course?"
  }'
## 🖼️ Request with Screenshot (base64 image)
{
  "question": "Please answer based on this screenshot:",
  "image": "<base64_encoded_image>"
}
##✅ Response Format
{
  "answer": "Yes, GitHub Copilot is considered an AI tool...",
  "links": [
    {
      "url": "https://tds.s-anand.net/#/github-copilot",
      "text": "GitHub Copilot"
    },
    {
      "url": "https://discourse.onlinedegree.iitm.ac.in/t/ga5-question-clarification/155939/4",
      "text": "GA5 clarification"
    }
  ]
}
##⚙️ Technologies
  -FastAPI + Uvicorn
  -OpenAI via AIPROXY
  -FAISS for vector search
  -pytesseract for OCR
  -dotenv for local .env support


