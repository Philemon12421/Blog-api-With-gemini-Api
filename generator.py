import os
import json
import re
import math
from google import genai
from google.genai import types


class ArticleGenerator:
    """Generates original AdSense-optimized blog articles using Gemini AI"""

    def __init__(self):
        api_key = os.environ.get("GEMINI_API_KEY", "placeholder")
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.0-flash"

    async def generate(self, topic, news, tone="informative", word_count=1200, audience="general audience"):
        research = self._build_research(news)

        prompt = f"""You are a professional SEO content writer. Your job is to write 100% ORIGINAL blog articles.

RULES:
- Never copy from sources. Always synthesize into fresh original writing.
- Follow Google AdSense quality guidelines (valuable, original, well-structured content)
- Respond with valid JSON ONLY. No markdown fences. No text before or after the JSON.

ARTICLE DETAILS:
- Topic: {topic}
- Target audience: {audience}
- Tone: {tone}
- Target word count: {word_count} words

RESEARCH MATERIAL (use as reference only, do NOT copy):
{research}

Return this exact JSON structure:
{{
  "title": "Compelling SEO title between 50-60 characters",
  "slug": "url-friendly-slug-here",
  "meta_description": "Meta description between 150-160 characters with primary keyword",
  "introduction": "Write 2-3 engaging opening paragraphs here",
  "sections": [
    {{
      "heading": "Section Heading Here",
      "level": 2,
      "content": "Write 3-4 detailed paragraphs of original content here",
      "key_points": ["Key point one", "Key point two", "Key point three"]
    }}
  ],
  "conclusion": "Write a strong 2-paragraph conclusion with a call to action",
  "faq": [
    {{"question": "Frequently asked question?", "answer": "Detailed 2-3 sentence answer"}},
    {{"question": "Second question?", "answer": "Detailed answer"}},
    {{"question": "Third question?", "answer": "Detailed answer"}}
  ],
  "seo": {{
    "primary_keyword": "main target keyword",
    "secondary_keywords": ["keyword 2", "keyword 3", "keyword 4", "keyword 5"],
    "meta_title": "SEO Page Title | Your Blog",
    "focus_keyphrase": "exact focus keyphrase",
    "readability_score": "Good",
    "keyword_density": 1.5
  }},
  "adsense_tips": [
    {{"placement": "After introduction", "reason": "High viewability, readers are engaged", "ad_type": "Display/Responsive"}},
    {{"placement": "Between section 2 and 3", "reason": "Mid-content high engagement zone", "ad_type": "In-article"}},
    {{"placement": "Before conclusion", "reason": "High intent, end of content", "ad_type": "Display/Responsive"}}
  ],
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
}}

IMPORTANT: Write at least {word_count} words across introduction + all sections + conclusion combined.
Include exactly 5-7 sections. Each section must have at least 200 words of content."""

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.8,
                max_output_tokens=4096,
            )
        )

        raw = response.text.strip()
        data = self._parse_json(raw)

        # Build HTML and Markdown
        data["html_content"] = self._build_html(data)
        data["markdown_content"] = self._build_markdown(data)
        data["word_count"] = self._count_words(data)
        data["reading_time"] = f"{math.ceil(data['word_count'] / 200)} min read"
        return data

    def _build_research(self, news):
        lines = []
        for i, a in enumerate(news.get("articles", [])[:6], 1):
            lines.append(f"[Source {i}] {a.get('publisher', '')} — {a.get('title', '')}")
            text = a.get("summary", "")
            if text:
                lines.append(f"  Summary: {text[:350]}")
        facts = news.get("key_facts", [])
        if facts:
            lines.append("\nKEY FACTS:")
            for f in facts[:8]:
                lines.append(f"  • {f}")
        return "\n".join(lines) if lines else f"Write a comprehensive article about: {news.get('topic', '')}"

    def _build_html(self, data):
        parts = []

        # Schema markup for SEO
        parts.append(f"""<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"Article","headline":"{self._esc(data.get('title',''))}","description":"{self._esc(data.get('meta_description',''))}"}}
</script>""")

        parts.append(f'<h1>{self._esc(data.get("title", ""))}</h1>')

        intro = data.get("introduction", "")
        if intro:
            parts.append(f'<div class="intro">{self._to_paras(intro)}</div>')

        parts.append("<!-- ADSENSE: After intro — Responsive Display Ad -->")

        for i, section in enumerate(data.get("sections", [])):
            level = section.get("level", 2)
            heading = self._esc(section.get("heading", ""))
            content = section.get("content", "")
            key_points = section.get("key_points", [])

            parts.append(f'<h{level} id="{self._slugify(heading)}">{heading}</h{level}>')
            parts.append(f'<div class="section-content">{self._to_paras(content)}</div>')

            if key_points:
                items = "".join(f"<li>{self._esc(p)}</li>" for p in key_points)
                parts.append(f'<ul class="key-points">{items}</ul>')

            if (i + 1) % 3 == 0:
                parts.append(f"<!-- ADSENSE: Mid-content — In-Article Ad -->")

        parts.append("<!-- ADSENSE: Before conclusion — Display Ad -->")

        conclusion = data.get("conclusion", "")
        if conclusion:
            parts.append(f'<h2 id="conclusion">Conclusion</h2>')
            parts.append(f'<div class="conclusion">{self._to_paras(conclusion)}</div>')

        faq = data.get("faq", [])
        if faq:
            parts.append('<section class="faq" itemscope itemtype="https://schema.org/FAQPage">')
            parts.append('<h2 id="faq">Frequently Asked Questions</h2>')
            for item in faq:
                q = self._esc(item.get("question", ""))
                a = self._esc(item.get("answer", ""))
                parts.append(f"""<div itemscope itemprop="mainEntity" itemtype="https://schema.org/Question">
<h3 itemprop="name">{q}</h3>
<div itemscope itemprop="acceptedAnswer" itemtype="https://schema.org/Answer">
<p itemprop="text">{a}</p>
</div></div>""")
            parts.append('</section>')

        parts.append("<!-- ADSENSE: After FAQ — Final Ad -->")
        return "\n".join(parts)

    def _build_markdown(self, data):
        parts = [
            f"# {data.get('title', '')}",
            f"\n> {data.get('meta_description', '')}",
            f"\n{data.get('introduction', '')}",
        ]
        for section in data.get("sections", []):
            level = "#" * section.get("level", 2)
            parts.append(f"\n{level} {section.get('heading', '')}")
            parts.append(section.get("content", ""))
            for kp in section.get("key_points", []):
                parts.append(f"- {kp}")
        parts.append(f"\n## Conclusion\n{data.get('conclusion', '')}")
        parts.append("\n## Frequently Asked Questions")
        for item in data.get("faq", []):
            parts.append(f"\n**{item.get('question', '')}**\n{item.get('answer', '')}")
        return "\n".join(parts)

    def _count_words(self, data):
        text = " ".join([
            data.get("introduction", ""),
            data.get("conclusion", ""),
            *[s.get("content", "") for s in data.get("sections", [])]
        ])
        return len(text.split())

    def _to_paras(self, text):
        return "".join(
            f"<p>{self._esc(p.strip())}</p>"
            for p in text.split("\n") if p.strip()
        )

    def _esc(self, text):
        return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

    def _slugify(self, text):
        return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")

    def _parse_json(self, text):
        # Remove markdown fences if present
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
        text = re.sub(r"\s*```\s*$", "", text, flags=re.MULTILINE)
        text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to extract JSON object
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                return json.loads(match.group())
            raise ValueError(f"Could not parse Gemini response as JSON.\nRaw response:\n{text[:500]}")
