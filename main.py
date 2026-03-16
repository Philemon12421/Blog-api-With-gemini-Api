from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uuid, os
from datetime import datetime
from generator import ArticleGenerator
from scraper import NewsScraper
from images import ImageFinder

app = FastAPI(title="AI Blog Generator", version="3.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
jobs = {}
scraper = NewsScraper()
generator = ArticleGenerator()
image_finder = ImageFinder()

class ArticleRequest(BaseModel):
    topic: str
    category: Optional[str] = "general"
    tone: Optional[str] = "informative"
    word_count: Optional[int] = 1200
    audience: Optional[str] = "general audience"
    image_count: Optional[int] = 3

@app.get("/")
async def root():
    return {"name": "AI Blog Generator (Gemini FREE)", "version": "3.0.0", "status": "running"}

@app.get("/trending")
async def trending(category: str = "general", limit: int = 10):
    return {"topics": await scraper.get_trending(category, limit)}

@app.post("/generate")
async def gen_async(req: ArticleRequest, bg: BackgroundTasks):
    jid = str(uuid.uuid4())
    jobs[jid] = {"status": "pending", "step": "queued"}
    bg.add_task(run_job, jid, req)
    return {"job_id": jid, "poll_url": "/status/" + jid, "result_url": "/article/" + jid}

@app.post("/generate/sync")
async def gen_sync(req: ArticleRequest):
    return await build(req)

@app.get("/status/{jid}")
async def get_status(jid: str):
    if jid not in jobs: raise HTTPException(404, "Not found")
    return jobs[jid]

@app.get("/article/{jid}")
async def get_article(jid: str):
    if jid not in jobs: raise HTTPException(404, "Not found")
    j = jobs[jid]
    if j["status"] == "failed": raise HTTPException(500, j.get("error"))
    if j["status"] != "completed": raise HTTPException(202, "Not ready: " + j.get("step",""))
    return j["article"]

async def run_job(jid, req):
    try:
        jobs[jid]["status"] = "processing"
        a = await build(req, jid)
        jobs[jid].update({"status": "completed", "article": a})
    except Exception as e:
        jobs[jid].update({"status": "failed", "error": str(e)})

async def build(req, jid=None):
    def step(s):
        if jid and jid in jobs: jobs[jid]["step"] = s

    step("scraping news")
    news = await scraper.scrape(req.topic, req.category or "general", 5)

    step("generating with Gemini")
    article = await generator.generate(
        req.topic, news,
        req.tone or "informative",
        req.word_count or 1200,
        req.audience or "general audience"
    )

    step("finding images")
    imgs = await image_finder.find(req.topic, req.image_count or 3)

    step("building article")
    article["images"] = imgs
    article["html_content"] = generator.build_html(article, images=imgs)
    article["markdown_content"] = generator.build_markdown(article)
    article["sources"] = news.get("sources", [])
    article["topic"] = req.topic
    article["category"] = req.category or "general"
    article["generated_at"] = datetime.utcnow().isoformat()
    article["id"] = jid or str(uuid.uuid4())
    return article
