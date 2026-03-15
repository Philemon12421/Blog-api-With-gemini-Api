# 🤖 AI Blog Article Generator API
### 100% FREE — Powered by Google Gemini • No Credit Card Needed

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/YOUR_USERNAME/blog-generator/blob/main/Blog_Generator_Gemini.ipynb)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)](https://fastapi.tiangolo.com)
[![Gemini](https://img.shields.io/badge/Gemini-2.0--flash-orange)](https://aistudio.google.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🚀 Run in Google Colab (One Click)

Click the **Open in Colab** badge above — runs entirely in your browser, nothing to install.

**You only need:**
- ✅ A Google account
- ✅ A free Gemini API key → [aistudio.google.com/apikey](https://aistudio.google.com/apikey)

---

## 💡 How It Works

```
Your Topic
    ↓
Scrape Google News + RSS feeds (BBC, CNN, TechCrunch, Reuters...)
    ↓
Gemini AI writes 100% ORIGINAL article (never copies sources)
    ↓
Find free images (Unsplash / Pexels / placeholders)
    ↓
Output: HTML + Markdown + JSON with SEO data + AdSense placement hints
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | API info + status |
| `GET` | `/docs` | Interactive Swagger UI |
| `POST` | `/generate/sync` | Generate article (waits 20-40s) |
| `POST` | `/generate` | Start async job (returns job_id) |
| `GET` | `/status/{job_id}` | Poll async job status |
| `GET` | `/article/{job_id}` | Get completed article |
| `GET` | `/trending` | Get trending news topics |

---

## 📦 Example Request

```json
POST /generate/sync
{
  "topic": "how to make money online with AI tools in 2025",
  "category": "tech",
  "tone": "informative",
  "word_count": 1200,
  "audience": "entrepreneurs and content creators",
  "image_count": 3
}
```

## 📦 Example Response

```json
{
  "title": "10 Proven Ways to Make Money With AI Tools in 2025",
  "slug": "make-money-ai-tools-2025",
  "meta_description": "Discover 10 proven ways to earn income using AI tools...",
  "word_count": 1247,
  "reading_time": "7 min read",
  "seo": {
    "primary_keyword": "make money with AI tools",
    "secondary_keywords": ["AI side hustle", "AI income 2025"],
    "readability_score": "Good"
  },
  "adsense_tips": [
    {"placement": "After introduction", "ad_type": "Display/Responsive"},
    {"placement": "Mid-content", "ad_type": "In-article"},
    {"placement": "Before conclusion", "ad_type": "Display/Responsive"}
  ],
  "html_content": "<h1>...</h1><!-- ADSENSE: After intro -->...",
  "markdown_content": "# 10 Proven Ways...",
  "images": [{"url": "https://...", "alt": "...", "license": "Free"}],
  "sources": [{"title": "...", "publisher": "TechCrunch"}]
}
```

---

## 🗂️ File Structure

```
blog-generator/
├── Blog_Generator_Gemini.ipynb  ← Open this in Google Colab
├── main.py                      ← FastAPI app & endpoints
├── generator.py                 ← Gemini AI article generation
├── scraper.py                   ← News scraping (Google News + RSS)
├── images.py                    ← Image search (Unsplash/Pexels)
├── requirements.txt             ← Python dependencies
├── .env.example                 ← Environment variable template
├── .gitignore
└── README.md
```

---

## 🛠️ Local Setup (Optional)

```bash
# 1. Clone
git clone https://github.com/YOUR_USERNAME/blog-generator.git
cd blog-generator

# 2. Install
pip install -r requirements.txt

# 3. Set env variables
cp .env.example .env
# Edit .env — add your GEMINI_API_KEY

# 4. Run
uvicorn main:app --reload --port 8000

# 5. Open docs
# http://localhost:8000/docs
```

---

## 🔑 API Keys

| Key | Required | Free? | Get it |
|-----|----------|-------|--------|
| `GEMINI_API_KEY` | ✅ Yes | ✅ Yes | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |
| `UNSPLASH_ACCESS_KEY` | ❌ No | ✅ Yes | [unsplash.com/developers](https://unsplash.com/developers) |
| `PEXELS_API_KEY` | ❌ No | ✅ Yes | [pexels.com/api](https://www.pexels.com/api/) |

Without image keys, the API uses free placeholder images automatically.

---

## ✅ AdSense Optimization

Every article includes:
- ✅ 1000–1500 words of 100% original content
- ✅ Proper H1 → H2 → H3 heading structure
- ✅ FAQ section (boosts Google rich results)
- ✅ Article schema structured data
- ✅ AdSense slot comments in HTML
- ✅ Meta description for click-through rate
- ✅ Image alt text for accessibility
- ✅ SEO keyword data (primary + secondary)

---

## 📜 License

MIT — free to use, modify, and deploy commercially.
# Blog-api-With-gemini-Api
