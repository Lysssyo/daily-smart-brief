import requests
import re
import json
import sys
import os
from google import genai
from google.genai import types

from core.config import GEMINI_API_KEY, APP_SETTINGS
from core.utils import load_text_file
from core.renderer import Renderer
from pipelines.base import BasePipeline

class GitHubBriefPipeline(BasePipeline):
    def __init__(self):
        self.renderer = Renderer()
        self.prompt_path = os.path.join("assets", "prompts", "github_prompt.md")
        self.template_path = os.path.join("assets", "templates", "github.mjml")
        # 加载配置
        self.config = APP_SETTINGS.get("github", {})

    def fetch_data(self):
        print("1. 正在获取 GitHub Trending 和 Hacker News 数据...")

        # 1. GitHub 请求
        gh_url = "https://github.com/trending?since=daily"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        try:
            gh_resp = requests.get(gh_url, headers=headers, timeout=10)
            gh_html = gh_resp.text
        except Exception as e:
            print(f"GitHub 请求失败: {e}")
            gh_html = ""

        # 2. Hacker News 请求
        hn_url = "http://hn.algolia.com/api/v1/search_by_date?query=github.com&tags=story&numericFilters=points>50&hitsPerPage=15"
        try:
            hn_resp = requests.get(hn_url, timeout=10)
            hn_json = hn_resp.text
        except Exception as e:
            print(f"HN 请求失败: {e}")
            hn_json = "{}"

        return gh_html, hn_json

    def preprocess_data(self, gh_html: str, hn_json: str) -> str:
        print("2. 正在预处理和合并数据...")

        gh_items = {}

        # GitHub 正则模式
        pattern_block = r'<article class="Box-row">([\s\S]*?)<\/article>'
        pattern_name = r'<h2 class="h3 lh-condensed">[\s\S]*?href="\/([^\"]+)"'
        pattern_desc = r'<p class="col-9 color-fg-muted my-1 pr-4">([\s\S]*?)<\/p>'
        pattern_lang = r'itemprop="programmingLanguage">([^<]+)<\/span>'
        pattern_stars = r'(\d+|[\d,]+) stars today'

        articles = re.findall(pattern_block, gh_html)
        for article in articles:
            try:
                name_match = re.search(pattern_name, article)
                if not name_match: continue
                name = name_match.group(1).strip()
                url = f"https://github.com/{name}"

                desc_match = re.search(pattern_desc, article)
                desc = desc_match.group(1).strip().replace('\n', ' ') if desc_match else "暂无描述"

                lang_match = re.search(pattern_lang, article)
                lang = lang_match.group(1).strip() if lang_match else "未知"

                stars_match = re.search(pattern_stars, article)
                stars = stars_match.group(1).strip() if stars_match else "0"

                gh_items[url] = f"【官方 Trending】{name}\n语言: {lang} | 今日星增: {stars}\n简介: {desc}\nURL: {url}"
            except:
                continue

        # HN 解析
        hn_items = []
        try:
            if not hn_json: hn_json = "{}"
            data_json = json.loads(hn_json)
            hits = data_json.get('hits', [])

            for hit in hits:
                url = hit.get('url', '')
                if not url or 'github.com' not in url: continue

                clean_url = url.split('?')[0].rstrip('/')
                title = hit.get('title', '无标题')
                points = hit.get('points', 0)

                is_duplicate = False
                for gh_url in gh_items.keys():
                    if clean_url.lower() == gh_url.lower():
                        gh_items[gh_url] = "【双榜 Trending】" + gh_items[gh_url][16:] + f"\n(HN 热度: {points})"
                        is_duplicate = True
                        break

                if not is_duplicate:
                    hn_items.append(f"【HN 热门】{title}\nHN 热度: {points}\nURL: {url}")
        except Exception as e:
            hn_items.append(f"HN 解析错误: {str(e)}")

        final_list = list(gh_items.values())[:8] + hn_items[:5]
        return "\n---\n".join(final_list)

    def analyze_with_gemini(self, raw_text: str):
        print("3. 正在调用 Gemini 进行深度分析...")

        if not GEMINI_API_KEY:
            print("错误: 缺少 GEMINI_API_KEY。")
            sys.exit(1)

        client_genai = genai.Client(api_key=GEMINI_API_KEY)
        prompt_content = load_text_file(self.prompt_path)
        model_name = self.config.get("model", "gemini-2.0-flash-exp")

        try:
            response = client_genai.models.generate_content(
                model=model_name,
                contents=f"以下是今日抓取的技术热榜数据，请分析：\n\n{raw_text}",
                config=types.GenerateContentConfig(
                    system_instruction=prompt_content,
                    response_mime_type="application/json",
                    temperature=0.7
                )
            )
            return response.text
        except Exception as e:
            print(f"Gemini API 调用失败: {e}")
            return None

    def run(self):
        # 步骤 1: 获取并预处理
        gh_data, hn_data = self.fetch_data()
        raw_input = self.preprocess_data(gh_data, hn_data)
        
        # 步骤 2: LLM 生成
        json_str = self.analyze_with_gemini(raw_input)

        if not json_str:
            print("错误: 未从 Gemini 接收到数据")
            sys.exit(1)

        # 步骤 3: JSON 解析
        print("正在解析 JSON...")
        clean_json_str = json_str.strip()
        if clean_json_str.startswith("```json"):
            clean_json_str = clean_json_str[7:]
        if clean_json_str.endswith("```"):
            clean_json_str = clean_json_str[:-3]
        
        try:
            data = json.loads(clean_json_str.strip())
            print("JSON 解析成功")
        except json.JSONDecodeError as e:
            print(f"JSON 解码错误: {e}")
            print(f"原始内容: {json_str}")
            sys.exit(1)

        # 步骤 4: 渲染与发布
        headline = self.config.get("subject", "Github Trending")
        sender_name = self.config.get("sender", "Gemini")
        
        template_str = load_text_file(self.template_path)
        
        self.renderer.render_and_publish(template_str, data, headline, sender=sender_name)
