import requests
import sys
from jinja2 import Template
from core.config import RENDER_API_URL

class Renderer:
    def __init__(self, render_api_url=None):
        self.render_api_url = render_api_url or RENDER_API_URL

    def render_and_publish(self, template_str, data, subject, sender="Daily Smart Brief"):
        """
        使用提供的数据渲染 MJML 模板并通过 API 发布。
        
        参数:
            template_str (str): MJML 模板字符串。
            data (dict): 传递给模板上下文的数据字典。
            subject (str): 简报的主题/标题。
            sender (str): 发送者的名称 (例如 "Gemini", "Grok")。
        """
        print("正在渲染 MJML 模板...")
        try:
            template = Template(template_str)
            # 将数据字典解包为模板的参数
            rendered_mjml = template.render(**data)
            print("模板渲染完成。")
        except Exception as e:
            print(f"渲染模板出错: {e}")
            sys.exit(1)

        print("正在请求渲染服务...")
        try:
            payload = {
                "subject": subject,
                "mjml_template": rendered_mjml,
                "sender": sender
            }

            resp = requests.post(self.render_api_url, json=payload)

            if resp.status_code == 200:
                print("成功！日报已生成。")
            else:
                print(f"API 请求失败: {resp.status_code} - {resp.text}")
                sys.exit(1)

        except Exception as e:
            print(f"网络请求异常: {e}")
            sys.exit(1)
