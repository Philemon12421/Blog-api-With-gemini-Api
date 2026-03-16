import os, json, re, math
from google import genai
from google.genai import types

class ArticleGenerator:
    def __init__(self):
        api_key = os.environ.get("GEMINI_API_KEY", "placeholder")
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.5-flash"

    async def generate(self, topic, news, tone="informative", word_count=1200, audience="general audience"):
        research = self._build_research(news)
        prompt = (
            "You are a professional SEO blog writer. Write 100% ORIGINAL content.\n"
            "Respond with valid JSON ONLY. No markdown fences. No extra text.\n\n"
            "TOPIC: " + topic + "\n"
            "AUDIENCE: " + audience + "\n"
            "TONE: " + tone + "\n"
            "WORD COUNT: " + str(word_count) + "\n\n"
            "RESEARCH (reference only):\n" + research + "\n\n"
            "Return this JSON structure:\n"
            '{"title":"SEO title","slug":"url-slug","meta_description":"150 char description",'
            '"introduction":"2-3 paragraphs of intro text",'
            '"sections":[{"heading":"Section Title","level":2,"content":"3-4 paragraphs","key_points":["point1","point2","point3"]}],'
            '"conclusion":"2 paragraph conclusion",'
            '"faq":[{"question":"Q1?","answer":"Answer 1"},{"question":"Q2?","answer":"Answer 2"},{"question":"Q3?","answer":"Answer 3"}],'
            '"seo":{"primary_keyword":"main keyword","secondary_keywords":["kw2","kw3","kw4"],"readability_score":"Good"},'
            '"adsense_tips":[{"placement":"After introduction","ad_type":"Display"},{"placement":"Mid-content","ad_type":"In-article"},{"placement":"Before conclusion","ad_type":"Display"}],'
            '"tags":["tag1","tag2","tag3"]}\n\n'
            "Write " + str(word_count) + "+ words. Include 5-7 sections."
        )
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.8, max_output_tokens=8192)
        )
        raw = response.text.strip()
        data = self._parse_json(raw)
        data["word_count"] = self._count_words(data)
        data["reading_time"] = str(math.ceil(data["word_count"] / 200)) + " min read"
        return data

    def build_html(self, data, images=None):
        p = []
        p.append("<h1>" + self._e(data.get("title", "")) + "</h1>")
        if images and len(images) > 0:
            p.append(self._img_html(images[0]))
        if data.get("introduction"):
            p.append("<div class='intro'>" + self._ps(data["introduction"]) + "</div>")
        p.append("<!-- ADSENSE: After intro -->")
        sections = data.get("sections", [])
        for i, s in enumerate(sections):
            lvl = str(s.get("level", 2))
            p.append("<h" + lvl + ">" + self._e(s.get("heading", "")) + "</h" + lvl + ">")
            p.append("<div>" + self._ps(s.get("content", "")) + "</div>")
            kps = s.get("key_points", [])
            if kps:
                p.append("<ul>" + "".join("<li>" + self._e(k) + "</li>" for k in kps) + "</ul>")
            if i == 2 and images and len(images) > 1:
                p.append(self._img_html(images[1]))
            if (i + 1) % 3 == 0:
                p.append("<!-- ADSENSE: Mid-content -->")
        p.append("<!-- ADSENSE: Before conclusion -->")
        if data.get("conclusion"):
            p.append("<h2>Conclusion</h2><div>" + self._ps(data["conclusion"]) + "</div>")
        if images and len(images) > 2:
            p.append(self._img_html(images[2]))
        faq = data.get("faq", [])
        if faq:
            p.append("<h2>Frequently Asked Questions</h2>")
            for item in faq:
                p.append("<h3>" + self._e(item.get("question", "")) + "</h3>")
                p.append("<p>" + self._e(item.get("answer", "")) + "</p>")
        p.append("<!-- ADSENSE: After FAQ -->")
        return "\n".join(p)

    def build_markdown(self, data):
        pts = ["# " + data.get("title", ""), "", data.get("introduction", ""), ""]
        for s in data.get("sections", []):
            pts += ["## " + s.get("heading", ""), s.get("content", ""), ""]
            for kp in s.get("key_points", []): pts.append("- " + kp)
        pts += ["", "## Conclusion", data.get("conclusion", ""), "", "## FAQ"]
        for item in data.get("faq", []): pts += ["**" + item.get("question", "") + "**", item.get("answer", ""), ""]
        return "\n".join(pts)

    def _img_html(self, image):
        url = image.get("url", "")
        alt = image.get("alt", "")
        caption = image.get("caption", "")
        credit_url = image.get("credit_url", "")
        img = "<img src='" + url + "' alt='" + alt + "' style='width:100%;height:auto;border-radius:8px;display:block' loading='lazy'>"
        if credit_url:
            credit = "<a href='" + credit_url + "' target='_blank' style='color:#666;font-size:0.8em'>" + caption + "</a>"
        else:
            credit = "<span style='color:#666;font-size:0.8em'>" + caption + "</span>"
        return "<figure style='margin:25px 0'>" + img + "<figcaption style='padding:6px 0;text-align:center'>" + credit + "</figcaption></figure>"

    def _build_research(self, news):
        lines = []
        for i, a in enumerate(news.get("articles", [])[:5], 1):
            lines.append("[" + str(i) + "] " + a.get("publisher", "") + " - " + a.get("title", ""))
            if a.get("summary"): lines.append("  " + a["summary"][:250])
        return "\n".join(lines) or "Write about: " + news.get("topic", "")

    def _count_words(self, data):
        return len(" ".join([data.get("introduction",""), data.get("conclusion","")] + [s.get("content","") for s in data.get("sections",[])]).split())

    def _ps(self, t):
        return "".join("<p>" + self._e(p.strip()) + "</p>" for p in t.split("\n") if p.strip())

    def _e(self, t):
        return str(t).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

    def _parse_json(self, text):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
        text = re.sub(r"\s*```\s*$", "", text, flags=re.MULTILINE).strip()
        try:
            return json.loads(text)
        except:
            m = re.search(r"\{.*\}", text, re.DOTALL)
            if m:
                try:
                    return json.loads(m.group())
                except:
                    pass
            raise ValueError("Cannot parse JSON: " + text[:200])
