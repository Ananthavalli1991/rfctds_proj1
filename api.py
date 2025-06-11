from fastapi import FastAPI, Request
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
import openai
import os
import base64
from io import BytesIO
from PIL import Image
import pytesseract
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

class Query(BaseModel):
    question: str
    image: str | None = None

# --- Scraper functions ---
def fetch_tds_pages():
    base_url = "https://tds.s-anand.net/"
    html = requests.get(base_url).text
    soup = BeautifulSoup(html, "html.parser")
    links = soup.select("a[href^='#/../']")
    pages = []
    for link in links[:3]:  # limit to 3 for speed
        full_url = base_url + link['href']
        try:
            page_html = requests.get(full_url).text
            page_soup = BeautifulSoup(page_html, "html.parser")
            text = page_soup.get_text("\n")
            pages.append({"url": full_url, "text": text})
        except:
            continue
    return pages

def fetch_discourse():
    discourse_url = "https://discourse.onlinedegree.iitm.ac.in/c/tds-jan-2025/63/l/latest.json"
    try:
        data = requests.get(discourse_url).json()
        posts = []
        for topic in data["topic_list"]["topics"][:3]:  # limit to 3
            posts.append({
                "url": f"https://discourse.onlinedegree.iitm.ac.in/t/{topic['slug']}/{topic['id']}",
                "text": topic.get("excerpt", "")
            })
        return posts
    except:
        return []

# --- OCR ---
def extract_text_from_image(base64_image):
    try:
        image_data = base64.b64decode(base64_image)
        image = Image.open(BytesIO(image_data))
        text = pytesseract.image_to_string(image)
        return text[:1000]  # limit to first 1000 chars
    except:
        return ""

# --- Matching ---
def match_docs(question, docs):
    return [doc for doc in docs if question.lower() in doc["text"].lower()][:3]

# --- LLM Prompting ---
def ask_llm(question, docs):
    context = "\n\n".join([f"{d['text']}\nSOURCE: {d['url']}" for d in docs])
    prompt = f"""
You are a helpful assistant for TDS students.
Answer the question using the context below.
Include the most relevant links.

Question: {question}

Context:
{context}
"""
    res = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return res.choices[0].message.content, docs

@app.post("/api/")
async def answer_question(q: Query):
    extracted_text = extract_text_from_image(q.image) if q.image else ""
    if extracted_text:
        print("Extracted text from image:\n", extracted_text[:300])

    full_question = q.question + "\n" + extracted_text if extracted_text else q.question
    tds_docs = fetch_tds_pages()
    disc_docs = fetch_discourse()
    all_docs = tds_docs + disc_docs
    matched = match_docs(full_question, all_docs)
    answer, used_docs = ask_llm(full_question, matched)
    links = [{"url": doc["url"], "text": doc["text"][:100]} for doc in used_docs]
    return {"answer": answer, "links": links}
