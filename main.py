from pipelines.github_brief import GitHubBriefPipeline
from pipelines.macro_brief import MacroBriefPipeline
import argparse
import sys
import os

# 确保当前目录在 python 路径中
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def main():
    # 1. 定义支持的管线
    pipelines = {
        "github": GitHubBriefPipeline,
        "macro": MacroBriefPipeline
    }

    # 2. 解析参数
    parser = argparse.ArgumentParser(description="Daily Smart Brief - 智能日报生成器")
    parser.add_argument(
        "--type",
        type=str,
        choices=list(pipelines.keys()) + ["all"],
        default="all",
        help="指定要生成的日报类型: github, macro, 或 all (默认)"
    )

    args = parser.parse_args()

    # 3. 确定要运行的任务
    tasks_to_run = []
    if args.type == "all":
        tasks_to_run = list(pipelines.values())
    else:
        tasks_to_run = [pipelines[args.type]]

    # 4. 执行
    print(f"🚀 开始执行 Daily Smart Brief... 模式: {args.type}")

    for PipelineClass in tasks_to_run:
        try:
            # 实例化并运行
            pipeline = PipelineClass()
            print(f"\n>> 正在运行管线: {PipelineClass.__name__}...")
            pipeline.run()
            print(f"✅ 完成: {PipelineClass.__name__}")
        except Exception as e:
            print(f"❌ 失败: {PipelineClass.__name__} 遇到错误: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
