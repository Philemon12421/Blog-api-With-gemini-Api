import requests
import json
import os
import sys

BASE_URL = "http://localhost:8000"

# CHANGE THIS TO YOUR TOPIC
TOPIC      = "how to make money online with AI tools in 2025"
CATEGORY   = "tech"
TONE       = "informative"
WORD_COUNT = 1200
AUDIENCE   = "entrepreneurs and content creators"
IMAGES     = 3

def check_server():
    try:
        r = requests.get(f"{BASE_URL}/", timeout=5)
        print("Server is running: " + r.json()["name"])
        return True
    except Exception:
        print("ERROR: Server is not running!")
        print("Go to your first terminal and run: python3 -m uvicorn main:app --reload --port 8000")
        return False

def generate_article():
    print("Generating article: " + TOPIC)
    print("Please wait 20-40 seconds...")
    try:
        r = requests.post(f"{BASE_URL}/generate/sync", json={
            "topic": TOPIC,
            "category": CATEGORY,
            "tone": TONE,
            "word_count": WORD_COUNT,
            "audience": AUDIENCE,
            "image_count": IMAGES,
        }, timeout=120)
        if r.status_code == 200:
            return r.json()
        else:
            print("ERROR " + str(r.status_code) + ": " + r.text[:300])
            return None
    except Exception as e:
        print("ERROR: " + str(e))
        return None

def save_files(article):
    slug = article.get("slug", "my-article")
    os.makedirs("output", exist_ok=True)

    css = "<style>body{font-family:Georgia,serif;max-width:800px;margin:40px auto;padding:20px;line-height:1.8;color:#333}h1{color:#1a1a2e}h2{color:#16213e;border-bottom:2px solid #e94560;padding-bottom:8px}ul{background:#f8f9fa;padding:15px 30px;border-radius:8px}</style>"
    html_doc = "<!DOCTYPE html><html><head><meta charset=UTF-8><meta name=description content=\"" + article["meta_description"] + "\"><title>" + article["title"] + "</title>" + css + "</head><body>" + article["html_content"] + "</body></html>"

    html_path = "output/" + slug + ".html"
    md_path   = "output/" + slug + ".md"
    json_path = "output/" + slug + ".json"

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_doc)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(article["markdown_content"])
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(article, f, indent=2, ensure_ascii=False)

    return html_path, md_path, json_path

def main():
    if not os.environ.get("GEMINI_API_KEY"):
        print("ERROR: GEMINI_API_KEY not set!")
        print("Run: export GEMINI_API_KEY=your_key_here")
        sys.exit(1)

    if not check_server():
        sys.exit(1)

    article = generate_article()
    if not article:
        sys.exit(1)

    print("----------------------------")
    print("Title:       " + article["title"])
    print("Words:       " + str(article["word_count"]))
    print("Reading:     " + article["reading_time"])
    print("Keyword:     " + article["seo"].get("primary_keyword", ""))
    print("----------------------------")

    html_path, md_path, json_path = save_files(article)
    print("FILES SAVED:")
    print("  HTML:     " + html_path)
    print("  Markdown: " + md_path)
    print("  JSON:     " + json_path)
    print("Done! Open the HTML file in your browser.")

if __name__ == "__main__":
    main()
