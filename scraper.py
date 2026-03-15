import asyncio
import aiohttp
import feedparser
import re
import logging
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from datetime import datetime
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class NewsScraper:
    HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    RSS_FEEDS = {
        "general": [
            "https://feeds.bbci.co.uk/news/rss.xml",
            "https://feeds.reuters.com/reuters/topNews",
        ],
        "tech": [
            "https://feeds.feedburner.com/TechCrunch",
            "https://www.theverge.com/rss/index.xml",
        ],
        "health": ["https://rss.medicalnewstoday.com/featurednews.xml"],
        "finance": ["https://www.cnbc.com/id/100003114/device/rss/rss.html"],
        "lifestyle": ["https://feeds.feedburner.com/huffingtonpost/wellness"],
    }

    def __init__(self):
        self.timeout = aiohttp.ClientTimeout(total=15)

    async def scrape(self, topic: str, category: str = "general", max_sources: int = 5) -> Dict:
        result = {
            "topic": topic,
            "category": category,
            "articles": [],
            "sources": [],
            "key_facts": [],
            "scraped_at": datetime.utcnow().isoformat(),
        }

        tasks = [
            self._google_news(topic, max_sources),
            self._rss_feeds(topic, category, max_sources),
        ]
        gathered = await asyncio.gather(*tasks, return_exceptions=True)
        for r in gathered:
            if isinstance(r, list):
                result["articles"].extend(r)

        result["articles"] = self._dedup(result["articles"])[:max_sources * 2]
        result["sources"] = [
            {"title": a.get("title", ""), "url": a.get("url", ""), "publisher": a.get("publisher", "")}
            for a in result["articles"]
        ]
        result["key_facts"] = self._extract_facts(result["articles"])
        return result

    async def get_trending(self, category: str = "general", limit: int = 10) -> List[Dict]:
        topics = []
        feeds = self.RSS_FEEDS.get(category, self.RSS_FEEDS["general"])
        async with aiohttp.ClientSession(headers=self.HEADERS, timeout=self.timeout) as session:
            for url in feeds[:2]:
                try:
                    async with session.get(url) as resp:
                        feed = feedparser.parse(await resp.text())
                        for entry in feed.entries[:5]:
                            topics.append({
                                "title": entry.get("title", ""),
                                "summary": entry.get("summary", "")[:200],
                                "url": entry.get("link", ""),
                                "source": feed.feed.get("title", "Unknown"),
                            })
                except Exception as e:
                    logger.warning(f"RSS trending error: {e}")
        return topics[:limit]

    async def _google_news(self, topic: str, max_results: int = 5) -> List[Dict]:
        articles = []
        url = f"https://news.google.com/rss/search?q={quote_plus(topic)}&hl=en-US&gl=US&ceid=US:en"
        try:
            async with aiohttp.ClientSession(headers=self.HEADERS, timeout=self.timeout) as session:
                async with session.get(url) as resp:
                    feed = feedparser.parse(await resp.text())
                    for entry in feed.entries[:max_results]:
                        articles.append({
                            "title": entry.get("title", ""),
                            "url": entry.get("link", ""),
                            "summary": self._clean(entry.get("summary", ""))[:400],
                            "published": entry.get("published", ""),
                            "publisher": entry.get("source", {}).get("title", "Google News"),
                        })
        except Exception as e:
            logger.warning(f"Google News error: {e}")
        return articles

    async def _rss_feeds(self, topic: str, category: str, max_sources: int = 3) -> List[Dict]:
        articles = []
        keywords = topic.lower().split()
        feeds = self.RSS_FEEDS.get(category, self.RSS_FEEDS["general"])
        async with aiohttp.ClientSession(headers=self.HEADERS, timeout=self.timeout) as session:
            for url in feeds:
                try:
                    async with session.get(url) as resp:
                        feed = feedparser.parse(await resp.text())
                        for entry in feed.entries:
                            title = entry.get("title", "").lower()
                            summary = entry.get("summary", "").lower()
                            score = sum(1 for kw in keywords if kw in title or kw in summary)
                            if score < 1 and len(keywords) > 1:
                                continue
                            articles.append({
                                "title": entry.get("title", ""),
                                "url": entry.get("link", ""),
                                "summary": self._clean(entry.get("summary", ""))[:400],
                                "publisher": feed.feed.get("title", "Unknown"),
                                "score": score,
                            })
                except Exception as e:
                    logger.warning(f"RSS error {url}: {e}")
        articles.sort(key=lambda x: x.get("score", 0), reverse=True)
        return articles[:max_sources]

    def _extract_facts(self, articles: List[Dict]) -> List[str]:
        facts = []
        for a in articles:
            text = a.get("summary", "")
            for sentence in re.split(r"(?<=[.!?])\s+", text)[:5]:
                s = sentence.strip()
                if 40 < len(s) < 300:
                    facts.append(s)
        return list(set(facts))[:15]

    def _dedup(self, articles: List[Dict]) -> List[Dict]:
        seen, unique = set(), []
        for a in articles:
            key = re.sub(r"\W+", "", a.get("title", "").lower())[:50]
            if key and key not in seen:
                seen.add(key)
                unique.append(a)
        return unique

    def _clean(self, text: str) -> str:
        return BeautifulSoup(text, "html.parser").get_text(separator=" ", strip=True) if text else ""
