from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime

from scraper import NewsScraper
from generator import ArticleGenerator
from images import ImageFinder

app = FastAPI(title="AI Blog Generator", version="3.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

jobs = {}
scraper = NewsScraper()
generator = ArticleGenerator()
images = ImageFinder()


class ArticleRequest(BaseModel):
    topic: str
    category: Optional[str] = "general"
    tone: Optional[str] = "informative"
    word_count: Optional[int] = 1200
    audience: Optional[str] = "general audience"
    image_count: Optional[int] = 3


@app.get("/")
async def root():
    return {
        "name": "AI Blog Generator (Gemini FREE)",
        "version": "3.0.0",
        "status": "running",
        "endpoints": {
            "POST /generate": "Generate article (returns job_id)",
            "GET /status/{job_id}": "Check job status",
            "GET /article/{job_id}": "Get completed article",
            "POST /generate/sync": "Generate and wait (30-60s)",
            "GET /trending": "Get trending topics"
        }
    }


@app.get("/trending")
async def trending(category: str = "general", limit: int = 10):
    topics = await scraper.get_trending(category=category, limit=limit)
    return {"topics": topics, "category": category}


@app.post("/generate")
async def generate_async(req: ArticleRequest, bg: BackgroundTasks):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "pending", "step": "queued", "created_at": datetime.utcnow().isoformat()}
    bg.add_task(run_job, job_id, req)
    return {"job_id": job_id, "status": "pending", "poll_url": f"/status/{job_id}", "result_url": f"/article/{job_id}"}


@app.post("/generate/sync")
async def generate_sync(req: ArticleRequest):
    return await build_article(req)


@app.get("/status/{job_id}")
async def get_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(404, "Job not found")
    return jobs[job_id]


@app.get("/article/{job_id}")
async def get_article(job_id: str):
    if job_id not in jobs:
        raise HTTPException(404, "Job not found")
    job = jobs[job_id]
    if job["status"] == "failed":
        raise HTTPException(500, job.get("error", "Unknown error"))
    if job["status"] != "completed":
        raise HTTPException(202, f"Not ready yet. Step: {job.get('step')}")
    return job["article"]


async def run_job(job_id: str, req: ArticleRequest):
    try:
        jobs[job_id]["status"] = "processing"
        article = await build_article(req, job_id)
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["article"] = article
        jobs[job_id]["completed_at"] = datetime.utcnow().isoformat()
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)


async def build_article(req: ArticleRequest, job_id: str = None):
    def step(s):
        if job_id and job_id in jobs:
            jobs[job_id]["step"] = s

    step("scraping news")
    news = await scraper.scrape(topic=req.topic, category=req.category, max_sources=5)

    step("generating article with Gemini AI")
    article = await generator.generate(
        topic=req.topic,
        news=news,
        tone=req.tone,
        word_count=req.word_count,
        audience=req.audience
    )

    step("finding images")
    imgs = await images.find(topic=req.topic, count=req.image_count)

    step("done")
    article["images"] = imgs
    article["sources"] = news.get("sources", [])
    article["topic"] = req.topic
    article["category"] = req.category
    article["generated_at"] = datetime.utcnow().isoformat()
    article["id"] = job_id or str(uuid.uuid4())
    return article
