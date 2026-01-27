from abc import ABC, abstractmethod


class BasePipeline(ABC):
    @abstractmethod
    def run(self):
        """
        执行管线以生成并发布简报。
        """
        pass
