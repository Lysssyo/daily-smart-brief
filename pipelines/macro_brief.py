import os
import json
import sys
from datetime import datetime
from xai_sdk import Client
from xai_sdk.tools import x_search
from xai_sdk.chat import user, system

from core.config import XAI_API_KEY, APP_SETTINGS
from core.utils import load_text_file
from core.renderer import Renderer
from pipelines.base import BasePipeline


class MacroBriefPipeline(BasePipeline):
    def __init__(self):
        self.renderer = Renderer()
        self.prompt_path = os.path.join("assets", "prompts", "macro_prompt.md")
        self.template_path = os.path.join("assets", "templates", "macro.mjml")
        # 加载配置
        self.config = APP_SETTINGS.get("macro", {})

    def get_grok_resp(self):
        print("正在创建 Grok 会话...")

        if not XAI_API_KEY:
            print("错误: 缺少 XAI_API_KEY。")
            sys.exit(1)

        client = Client(api_key=XAI_API_KEY)

        # 使用配置中指定的模型
        model_name = self.config.get("model", "grok-3")
        chat = client.chat.create(
            model=model_name,
            tools=[x_search()],
        )

        prompt_content = load_text_file(self.prompt_path)

        # 获取当前日期用于 Prompt
        current_date = datetime.now().strftime("%Y年%m月%d日")
        user_query_content = f"请执行上述 System Instruction，针对【{current_date}】这一天，进行全网搜索并生成 JSON 报表。"

        try:
            chat.append(system(prompt_content))
            query = user_query_content
        except NameError:
            print("警告: 未找到 system() 辅助函数，正在前置。")
            query = "System Instruction:\n" + prompt_content + "\n\nUser Query:\n" + user_query_content

        print(f"用户查询: {user_query_content}\n")
        chat.append(user(query))

        print("--- Grok 正在思考与搜索 ---")
        full_json_content = ""

        # 流式响应
        for response, chunk in chat.stream():
            if hasattr(chunk, 'tool_calls') and chunk.tool_calls:
                for tool_call in chunk.tool_calls:
                    print(f"\n[工具调用]: {tool_call.function.name} | 参数: {tool_call.function.arguments}")

            if chunk.content:
                print(chunk.content, end="", flush=True)
                full_json_content += chunk.content

        print("\n\n--- 搜索来源 ---")
        if hasattr(response, 'citations'):
            for url in response.citations:
                print(url)

        return full_json_content

    def run(self):
        # 步骤 1: 从 Grok 获取数据
        json_str = self.get_grok_resp()

        if not json_str:
            print("错误: 未从 Grok 接收到数据")
            sys.exit(1)

        # 步骤 2: 解析 JSON
        print("\n正在解析 JSON...")
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

        # 步骤 3: 渲染与发布
        headline = self.config.get("subject", "What's happening around the world?")
        sender_name = self.config.get("sender", "Grok")

        template_str = load_text_file(self.template_path)

        self.renderer.render_and_publish(template_str, data, headline, sender=sender_name)
