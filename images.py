import aiohttp
import os
import logging
logger = logging.getLogger(__name__)

class ImageFinder:
    def __init__(self):
        self.unsplash_key = os.environ.get("UNSPLASH_ACCESS_KEY", "")
        self.pexels_key = os.environ.get("PEXELS_API_KEY", "")

    async def find(self, topic, count=3):
        queries = self._queries(topic, count)
        images = []
        async with aiohttp.ClientSession() as session:
            for i, query in enumerate(queries[:count]):
                img = None
                # Try Unsplash first
                if self.unsplash_key:
                    img = await self._unsplash(session, query, i)
                # Fall back to Pexels
                if not img and self.pexels_key:
                    img = await self._pexels(session, query, i)
                # Fall back to placeholder
                if not img:
                    img = self._placeholder(query, i)
                images.append(img)
        return images

    def _queries(self, topic, count):
        words = topic.split()
        queries = [topic, " ".join(words[:3]), " ".join(words[:2])]
        while len(queries) < count:
            queries.append(topic)
        return queries[:count]

    async def _unsplash(self, session, query, index):
        try:
            async with session.get(
                "https://api.unsplash.com/search/photos",
                params={"query": query, "per_page": 1, "orientation": "landscape"},
                headers={"Authorization": "Client-ID " + self.unsplash_key}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    results = data.get("results", [])
                    if results:
                        p = results[0]
                        return {
                            "url": p["urls"]["regular"],
                            "thumb": p["urls"]["small"],
                            "alt": p.get("alt_description") or query,
                            "caption": "Photo by " + p["user"]["name"] + " on Unsplash",
                            "credit_url": p["user"]["links"]["html"],
                            "source": "unsplash",
                            "license": "Unsplash License (free for commercial use)",
                        }
                elif resp.status == 403:
                    logger.warning("Unsplash: invalid key")
                elif resp.status == 429:
                    logger.warning("Unsplash: rate limit hit, switching to Pexels")
        except Exception as e:
            logger.warning("Unsplash error: " + str(e))
        return None

    async def _pexels(self, session, query, index):
        try:
            async with session.get(
                "https://api.pexels.com/v1/search",
                params={"query": query, "per_page": 1, "orientation": "landscape"},
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
                            "caption": "Photo by " + p["photographer"] + " on Pexels",
                            "credit_url": p["photographer_url"],
                            "source": "pexels",
                            "license": "Pexels License (free for commercial use)",
                        }
                elif resp.status == 403:
                    logger.warning("Pexels: invalid key")
                elif resp.status == 429:
                    logger.warning("Pexels: rate limit hit")
        except Exception as e:
            logger.warning("Pexels error: " + str(e))
        return None

    def _placeholder(self, query, index):
        return {
            "url": "https://picsum.photos/seed/" + str(index+1) + "/1200/630",
            "thumb": "https://picsum.photos/seed/" + str(index+1) + "/400/210",
            "alt": query,
            "caption": "Set UNSPLASH_ACCESS_KEY or PEXELS_API_KEY for real photos",
            "credit_url": "",
            "source": "placeholder",
            "license": "placeholder",
        }

    def build_img_html(self, image):
        url = image.get("url", "")
        alt = image.get("alt", "")
        caption = image.get("caption", "")
        credit_url = image.get("credit_url", "")
        source = image.get("source", "")

        img_html = "<img src='" + url + "' alt='" + alt + "' style='width:100%;height:auto;border-radius:8px;display:block' loading='lazy'>"

        if credit_url:
            credit_html = "<a href='" + credit_url + "' target='_blank' rel='noopener' style='color:#666;font-size:0.8em;text-decoration:none'>" + caption + "</a>"
        else:
            credit_html = "<span style='color:#666;font-size:0.8em'>" + caption + "</span>"

        return "<figure style='margin:25px 0;padding:0'>" + img_html + "<figcaption style='padding:6px 0 0;text-align:center'>" + credit_html + "</figcaption></figure>"
