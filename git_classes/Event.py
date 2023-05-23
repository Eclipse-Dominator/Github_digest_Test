from datetime import datetime


class Event:
    def __init__(self, data, timestamp: datetime, description: str, link: str = None):
        self.data = data
        self.timestamp = timestamp
        self.description = description
        self.link = link

    def to_markdown(self) -> str:
        ret = f"{self.timestamp}: {self.description}"
        if self.link:
            ret += f"\n{self.link}"
        return ret