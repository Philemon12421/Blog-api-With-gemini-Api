import aiohttp
import os
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


class ImageFinder:
    def __init__(self):
        self.unsplash_key = os.environ.get("UNSPLASH_ACCESS_KEY", "")
        self.pexels_key = os.environ.get("PEXELS_API_KEY", "")

    async def find(self, topic: str, count: int = 3) -> List[Dict]:
        images = []
        queries = self._queries(topic, count)
        async with aiohttp.ClientSession() as session:
            for i, query in enumerate(queries[:count]):
                img = None
                if self.unsplash_key:
                    img = await self._unsplash(session, query)
                if not img and self.pexels_key:
                    img = await self._pexels(session, query)
                if not img:
                    img = self._placeholder(query, i)
                images.append(img)
        return images

    def _queries(self, topic: str, count: int) -> List[str]:
        words = topic.split()
        queries = [topic, " ".join(words[:3])]
        while len(queries) < count:
            queries.append(topic)
        return queries[:count]

    async def _unsplash(self, session, query: str) -> Dict:
        try:
            async with session.get(
                "https://api.unsplash.com/search/photos",
                params={"query": query, "per_page": 1, "orientation": "landscape"},
                headers={"Authorization": f"Client-ID {self.unsplash_key}"}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    results = data.get("results", [])
                    if results:
                        p = results[0]
                        return {
                            "url": p["urls"]["regular"],
                            "thumb": p["urls"]["thumb"],
                            "alt": p.get("alt_description") or query,
                            "caption": f"Photo by {p['user']['name']} on Unsplash",
                            "source": "unsplash",
                            "license": "Unsplash License (free commercial use)",
                        }
        except Exception as e:
            logger.warning(f"Unsplash: {e}")
        return None

    async def _pexels(self, session, query: str) -> Dict:
        try:
            async with session.get(
                "https://api.pexels.com/v1/search",
                params={"query": query, "per_page": 1},
                headers={"Authorization": self.pexels_key}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    photos = data.get("photos", [])
                    if photos:
                        p = photos[0]
                        return {
                            "url": p["src"]["large"],
                            "thumb": p["src"]["medium"],
                            "alt": p.get("alt") or query,
                            "caption": f"Photo by {p['photographer']} on Pexels",
                            "source": "pexels",
                            "license": "Pexels License (free commercial use)",
                        }
        except Exception as e:
            logger.warning(f"Pexels: {e}")
        return None

    def _placeholder(self, query: str, index: int) -> Dict:
        return {
            "url": f"https://picsum.photos/seed/{index + 1}/1200/630",
            "thumb": f"https://picsum.photos/seed/{index + 1}/400/210",
            "alt": f"{query} image",
            "caption": f"Image related to {query}",
            "source": "placeholder",
            "license": "Free placeholder — add UNSPLASH_ACCESS_KEY for real photos",
        }
