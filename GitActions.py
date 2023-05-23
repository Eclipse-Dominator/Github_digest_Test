from datetime import datetime

class Event:
    link: str
    txt: str
    timestamp: datetime

    def __init__(self, data, link, txt):
        self.data = data
        self.link = link
        self.txt = txt